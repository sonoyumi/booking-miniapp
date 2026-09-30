import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pytest
from conftest import ADMIN_ID, ANNA, LUCA, NOW, TZ, login

TODAY = NOW.astimezone(TZ).date()


def slot_ts(hour: int, day=TODAY) -> int:
    return int(datetime(day.year, day.month, day.day, hour, tzinfo=TZ).timestamp())


async def test_login_is_required(client):
    r = await client.get("/api/config")
    assert r.status_code == 401 and r.json()["detail"] == "open this page from Telegram"
    r = await client.get("/api/config", headers={"Authorization": "tma user=forged&hash=00"})
    assert r.status_code == 401


async def test_config_days_and_slots(client):
    config = (await client.get("/api/config", headers=login(ANNA))).json()
    assert config["shop"] == "Barbiere Alpino" and config["user"] == {"id": 100, "name": "Anna Rossi"}
    assert [s["id"] for s in config["services"]] == ["haircut", "beard"]

    days = (await client.get("/api/days", params={"service_id": "haircut"}, headers=login(ANNA))).json()
    assert [d["date"] for d in days] == [TODAY.isoformat(), "2026-10-06", "2026-10-07"]
    assert days[0] == {"date": "2026-10-05", "label": "Пн 05.10", "free": 3}

    slots = (
        await client.get("/api/slots", params={"service_id": "haircut", "day": "2026-10-05"}, headers=login(ANNA))
    ).json()
    assert [s["time"] for s in slots["slots"]] == ["10:00", "11:00", "12:00"]
    assert slots["slots"][0]["ts"] == slot_ts(10)


async def test_booking_flow_and_admin_notifications(client, sender):
    r = await client.post("/api/bookings", json={"service_id": "haircut", "ts": slot_ts(11)}, headers=login(ANNA))
    assert r.status_code == 201
    assert r.json()["when"] == "Пн 05.10 в 11:00" and r.json()["service"] == "Стрижка"
    assert sender.sent[-1][0] == ADMIN_ID and "Новая запись" in sender.sent[-1][1] and "Mini App" in sender.sent[-1][1]

    slots = (
        await client.get("/api/slots", params={"service_id": "beard", "day": "2026-10-05"}, headers=login(LUCA))
    ).json()
    assert [s["time"] for s in slots["slots"]] == ["10:00", "12:00"]  # 11:00 is gone for everybody
    days = (await client.get("/api/days", params={"service_id": "beard"}, headers=login(LUCA))).json()
    assert days[0]["free"] == 2

    mine = (await client.get("/api/bookings", headers=login(ANNA))).json()
    assert [(b["service"], b["when"]) for b in mine] == [("Стрижка", "Пн 05.10 в 11:00")]
    assert (await client.get("/api/bookings", headers=login(LUCA))).json() == []

    booking_id = mine[0]["id"]
    assert (await client.delete(f"/api/bookings/{booking_id}", headers=login(LUCA))).status_code == 404  # not his
    r = await client.delete(f"/api/bookings/{booking_id}", headers=login(ANNA))
    assert r.status_code == 200 and "Отмена записи" in sender.sent[-1][1]
    assert (await client.delete(f"/api/bookings/{booking_id}", headers=login(ANNA))).status_code == 404


async def test_same_slot_cannot_be_taken_twice(client):
    body = {"service_id": "haircut", "ts": slot_ts(10)}
    assert (await client.post("/api/bookings", json=body, headers=login(ANNA))).status_code == 201
    r = await client.post("/api/bookings", json=body, headers=login(LUCA))
    assert r.status_code == 409 and "just taken" in r.json()["detail"]


@pytest.mark.parametrize(
    ("body", "detail"),
    [
        ({"service_id": "haircut", "ts": slot_ts(10) + 420}, "not available"),  # 10:07 is not a slot
        ({"service_id": "haircut", "ts": slot_ts(9)}, "not available"),  # before opening hours
        ({"service_id": "haircut", "ts": slot_ts(10, TODAY.replace(day=20))}, "not available"),  # too far ahead
        ({"service_id": "massage", "ts": slot_ts(10)}, "service is not available"),
    ],
)
async def test_forged_requests_are_rejected(client, db, body, detail):
    r = await client.post("/api/bookings", json=body, headers=login(ANNA))
    assert r.status_code == 422 and detail in r.json()["detail"]
    assert await db.user_bookings(ANNA["id"], NOW) == []


async def test_closed_day_and_active_limit(client):
    r = await client.get("/api/slots", params={"service_id": "haircut", "day": "2026-10-20"}, headers=login(ANNA))
    assert r.status_code == 422
    for hour in (10, 11):
        await client.post("/api/bookings", json={"service_id": "haircut", "ts": slot_ts(hour)}, headers=login(ANNA))
    r = await client.post("/api/bookings", json={"service_id": "haircut", "ts": slot_ts(12)}, headers=login(ANNA))
    assert r.status_code == 429 and "2 upcoming bookings" in r.json()["detail"]


async def test_bot_and_mini_app_share_the_same_bookings(client, db):
    # Booked through the Telegram bot (booking-bot's own code) -> the Mini App does not offer that time.
    await db.book(
        user_id=300, user_name="Via bot", service_id="haircut", starts_at=datetime.fromtimestamp(slot_ts(12), TZ)
    )
    slots = (
        await client.get("/api/slots", params={"service_id": "haircut", "day": "2026-10-05"}, headers=login(ANNA))
    ).json()
    assert [s["time"] for s in slots["slots"]] == ["10:00", "11:00"]
    # Booked through the Mini App -> the bot's /my shows it.
    await client.post("/api/bookings", json={"service_id": "haircut", "ts": slot_ts(10)}, headers=login(ANNA))
    assert [b.service_id for b in await db.user_bookings(ANNA["id"], NOW)] == ["haircut"]


async def test_dev_mode_without_telegram(make_client):
    client = await make_client(dev_user_id=777)
    config = (await client.get("/api/config")).json()
    assert config["user"] == {"id": 777, "name": "Dev"}


async def test_page_and_static_files(client):
    page = await client.get("/")
    assert page.status_code == 200 and "telegram-web-app.js" in page.text
    assert (await client.get("/static/app.js")).status_code == 200
    assert (await client.get("/static/style.css")).status_code == 200
    assert (await client.get("/health")).json()["status"] == "ok"


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_frontend_script_parses():
    script = Path(__file__).resolve().parents[1] / "src" / "booking_miniapp" / "static" / "app.js"
    assert subprocess.run(["node", "--check", str(script)], capture_output=True).returncode == 0
