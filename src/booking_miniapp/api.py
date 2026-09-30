"""HTTP API and static files of the Mini App.

Every /api request carries `Authorization: tma <initData>`; the user comes from the verified
signature, never from the request body. Booking rules are booking-bot's own: Schedule.is_bookable
rejects forged times, the database's unique index rejects double bookings.

No `from __future__ import annotations` here: FastAPI reads the annotations at runtime.
"""

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Annotated

from booking_bot.db import Database
from booking_bot.services import Service, load_services, service_title
from booking_bot.texts import day_label, user_link, when
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from booking_miniapp import __version__
from booking_miniapp.auth import InitDataError, TgUser, validate_init_data
from booking_miniapp.config import Settings
from booking_miniapp.notify import Sender, notify_admins

logger = logging.getLogger(__name__)
STATIC = Path(__file__).parent / "static"


class BookingRequest(BaseModel):
    service_id: str
    ts: int  # unix time of the slot start, exactly as /api/slots returned it


def create_app(
    settings: Settings,
    db: Database | None = None,
    sender: Sender | None = None,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> FastAPI:
    schedule = settings.schedule
    tz = schedule.tz

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        own_db = db is None
        app.state.db = db or await Database.open(settings.database_path)
        app.state.services = load_services(settings.services_path)
        bot = None
        if sender is None:
            from aiogram import Bot

            bot = Bot(settings.bot_token)
        app.state.sender = sender or bot
        if settings.dev_user_id:
            logger.warning("DEV_USER_ID is set: requests without Telegram login act as user %s", settings.dev_user_id)
        yield
        if own_db:
            await app.state.db.close()
        if bot is not None:
            await bot.session.close()

    app = FastAPI(title="Booking Mini App", version=__version__, lifespan=lifespan, docs_url=None, redoc_url=None)

    def current_user(authorization: Annotated[str | None, Header()] = None) -> TgUser:
        if authorization and authorization.startswith("tma "):
            try:
                return validate_init_data(
                    authorization[4:], settings.bot_token, settings.init_data_max_age, now=clock().timestamp()
                )
            except InitDataError as exc:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from None
        if settings.dev_user_id:
            return TgUser(id=settings.dev_user_id, first_name="Dev")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "open this page from Telegram")

    User = Annotated[TgUser, Depends(current_user)]

    def get_db(request: Request) -> Database:
        return request.app.state.db

    def get_services(request: Request) -> dict[str, Service]:
        return request.app.state.services

    DB = Annotated[Database, Depends(get_db)]
    Services = Annotated[dict[str, Service], Depends(get_services)]

    def _service(services: dict[str, Service], service_id: str) -> Service:
        service = services.get(service_id)
        if service is None:
            raise HTTPException(422, "this service is not available")
        return service

    def _booking_view(booking, services: dict[str, Service]) -> dict:
        return {
            "id": booking.id,
            "service": service_title(services, booking.service_id),
            "when": when(booking.starts_at, tz),
            "ts": int(booking.starts_at.timestamp()),
        }

    @app.get("/api/config")
    async def config(user: User, services: Services):
        return {
            "shop": settings.shop_name,
            "timezone": str(tz),
            "user": {"id": user.id, "name": user.full_name},
            "services": [{"id": s.id, "title": s.title, "price": s.price} for s in services.values()],
        }

    @app.get("/api/days")
    async def days(service_id: str, user: User, services: Services, database: DB):
        _service(services, service_id)
        now = clock()
        open_days = schedule.days(now)
        if not open_days:
            return []
        first, last = schedule.slots(open_days[0]), schedule.slots(open_days[-1])
        booked = await database.booked_starts(first[0], last[-1] + schedule.slot) if first and last else set()
        return [
            {"date": d.isoformat(), "label": day_label(d), "free": len(schedule.free_slots(d, booked, now))}
            for d in open_days
        ]

    @app.get("/api/slots")
    async def slots(service_id: str, day: date, user: User, services: Services, database: DB):
        _service(services, service_id)
        now = clock()
        if day not in schedule.days(now):
            raise HTTPException(422, "this day is not open for booking")
        all_slots = schedule.slots(day)
        booked = await database.booked_starts(all_slots[0], all_slots[-1] + schedule.slot) if all_slots else set()
        return {
            "date": day.isoformat(),
            "label": day_label(day),
            "slots": [
                {"ts": int(s.timestamp()), "time": f"{s.astimezone(tz):%H:%M}"}
                for s in schedule.free_slots(day, booked, now)
            ],
        }

    @app.post("/api/bookings", status_code=status.HTTP_201_CREATED)
    async def book(body: BookingRequest, user: User, services: Services, database: DB, request: Request):
        service = _service(services, body.service_id)
        now = clock()
        slot = datetime.fromtimestamp(body.ts, UTC)
        if not schedule.is_bookable(slot, now):  # forged or stale times never reach the database
            raise HTTPException(422, "this time is not available")
        if len(await database.user_bookings(user.id, now)) >= settings.max_active_per_user:
            raise HTTPException(429, f"you already have {settings.max_active_per_user} upcoming bookings")
        booking_id = await database.book(
            user_id=user.id, user_name=user.full_name, service_id=service.id, starts_at=slot
        )
        if booking_id is None:
            raise HTTPException(409, "this time was just taken, choose another one")
        await notify_admins(
            request.app.state.sender,
            settings.admin_ids,
            f"🆕 Новая запись #{booking_id} (Mini App)\n{user_link(user.id, user.full_name)}\n"
            f"<b>{service.title}</b>, {when(slot, tz)}",
        )
        return {"id": booking_id, "service": service.title, "when": when(slot, tz), "ts": body.ts}

    @app.get("/api/bookings")
    async def my_bookings(user: User, services: Services, database: DB):
        return [_booking_view(b, services) for b in await database.user_bookings(user.id, clock())]

    @app.delete("/api/bookings/{booking_id}")
    async def cancel(booking_id: int, user: User, services: Services, database: DB, request: Request):
        booking = await database.cancel(booking_id, user.id)  # only the owner's own active booking
        if booking is None:
            raise HTTPException(404, "booking not found or already cancelled")
        title = service_title(services, booking.service_id)
        await notify_admins(
            request.app.state.sender,
            settings.admin_ids,
            f"❌ Отмена записи #{booking.id} (Mini App)\n{user_link(user.id, user.full_name)}\n"
            f"<b>{title}</b>, {when(booking.starts_at, tz)}",
        )
        return {"cancelled": booking.id}

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": __version__}

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app
