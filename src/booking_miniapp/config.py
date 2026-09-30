"""Settings from environment variables (.env in the current folder).

The schedule variables have the same names and meaning as in booking-bot: set them to the same
values, and point DATABASE_PATH and SERVICES_PATH to the bot's files, so both show the same slots.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from booking_bot.schedule import Schedule
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str = field(repr=False)  # checks the Mini App signature and sends notifications
    admin_ids: frozenset[int]
    schedule: Schedule
    database_path: Path
    services_path: Path
    shop_name: str = "Запись онлайн"
    webapp_url: str = ""  # public HTTPS address of the Mini App (for the menu button)
    init_data_max_age: int = 86_400  # seconds a Telegram login stays valid
    max_active_per_user: int = 3
    dev_user_id: int | None = None  # ONLY for local testing in a normal browser


def _int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    try:
        return int(raw) if raw else default
    except ValueError:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from None


def _ids(name: str, default: str = "") -> frozenset[int]:
    raw = os.getenv(name, "").strip() or default  # an empty line in .env means "use the default"
    try:
        return frozenset(int(part) for part in raw.replace(" ", "").split(",") if part)
    except ValueError:
        raise ValueError(f"{name} must be a comma-separated list of integers, got {raw!r}") from None


def load_settings(env_file: Path | None = Path(".env")) -> Settings:
    if env_file is not None:
        load_dotenv(env_file)
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is not set: the same token as the booking bot, in .env")
    tz_name = os.getenv("TIMEZONE", "").strip() or "Europe/Rome"
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        raise ValueError(f"Unknown TIMEZONE {tz_name!r}, use a name like Europe/Rome") from None
    schedule = Schedule(
        tz=tz,
        work_start=_int("WORK_START", 10),
        work_end=_int("WORK_END", 19),
        slot_minutes=_int("SLOT_MINUTES", 60),
        days_ahead=_int("DAYS_AHEAD", 7),
        work_days=_ids("WORK_DAYS", "1,2,3,4,5,6"),
    )
    url = os.getenv("WEBAPP_URL", "").strip()
    if url and not url.startswith("https://"):
        raise ValueError("WEBAPP_URL must start with https:// (Telegram opens Mini Apps only over HTTPS)")
    dev = os.getenv("DEV_USER_ID", "").strip()
    return Settings(
        bot_token=token,
        admin_ids=_ids("ADMIN_IDS"),
        schedule=schedule,
        database_path=Path(os.getenv("DATABASE_PATH", "").strip() or "data/bookings.db"),
        services_path=Path(os.getenv("SERVICES_PATH", "").strip() or "config/services.json"),
        shop_name=os.getenv("SHOP_NAME", "").strip() or "Запись онлайн",
        webapp_url=url,
        init_data_max_age=_int("INIT_DATA_MAX_AGE", 86_400),
        max_active_per_user=_int("MAX_ACTIVE_PER_USER", 3),
        dev_user_id=int(dev) if dev else None,
    )
