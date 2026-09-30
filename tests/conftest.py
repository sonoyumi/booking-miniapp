"""Shared fixtures: a fixed "now", booking-bot's real Database in memory, a recorded notifier,
and signed Telegram logins for two users."""

import json
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest
from booking_bot.db import Database
from booking_bot.schedule import Schedule

from booking_miniapp.api import create_app
from booking_miniapp.auth import sign
from booking_miniapp.config import Settings

TOKEN = "123456:TEST-TOKEN"
TZ = ZoneInfo("Europe/Rome")
NOW = datetime(2026, 10, 5, 6, 0, tzinfo=UTC)  # 08:00 in Rome, every slot of the day is still ahead
ANNA = {"id": 100, "first_name": "Anna", "last_name": "Rossi", "username": "anna"}
LUCA = {"id": 200, "first_name": "Luca"}
ADMIN_ID = 1


def login(user: dict, auth_date: float | None = None) -> dict[str, str]:
    fields = {"auth_date": str(int(auth_date or NOW.timestamp())), "query_id": "AAH", "user": json.dumps(user)}
    return {"Authorization": "tma " + sign(fields, TOKEN)}


class RecordingSender:
    def __init__(self) -> None:
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str, **kwargs) -> None:
        self.sent.append((chat_id, text))


@pytest.fixture
def settings(tmp_path) -> Settings:
    services = tmp_path / "services.json"
    services.write_text(
        json.dumps(
            [
                {"id": "haircut", "title": "Стрижка", "price": "25 €"},
                {"id": "beard", "title": "Борода", "price": "15 €"},
            ]
        )
    )
    return Settings(
        bot_token=TOKEN,
        admin_ids=frozenset({ADMIN_ID}),
        schedule=Schedule(
            tz=TZ, work_start=10, work_end=13, slot_minutes=60, days_ahead=3, work_days=frozenset(range(1, 8))
        ),
        database_path=Path(":memory:"),
        services_path=services,
        shop_name="Barbiere Alpino",
        max_active_per_user=2,
    )


@pytest.fixture
async def db():
    database = await Database.open(":memory:")
    yield database
    await database.close()


@pytest.fixture
def sender():
    return RecordingSender()


@pytest.fixture
def make_client(settings, db, sender):
    async def factory(**overrides):
        app = create_app(Settings(**{**settings.__dict__, **overrides}), db=db, sender=sender, clock=lambda: NOW)
        ctx = app.router.lifespan_context(app)
        await ctx.__aenter__()
        client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://miniapp")
        factory.cleanup.append((client, ctx))
        return client

    factory.cleanup = []
    yield factory


@pytest.fixture
async def client(make_client):
    c = await make_client()
    yield c
    for http, ctx in make_client.cleanup:
        await http.aclose()
        await ctx.__aexit__(None, None, None)
