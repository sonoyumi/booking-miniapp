"""Messages to the owner about new bookings and cancellations (same texts style as the bot)."""

from __future__ import annotations

import logging
from typing import Protocol

from booking_bot.texts import user_link

logger = logging.getLogger(__name__)


class Sender(Protocol):
    async def send_message(self, chat_id: int, text: str, **kwargs) -> object: ...


async def notify_admins(sender: Sender | None, admin_ids: frozenset[int], text: str) -> None:
    if sender is None:
        return
    for admin_id in sorted(admin_ids):
        try:
            await sender.send_message(admin_id, text, parse_mode="HTML")
        except Exception:  # one admin who blocked the bot must not break the booking
            logger.warning("Cannot notify admin %s", admin_id)


__all__ = ["notify_admins", "user_link", "Sender"]
