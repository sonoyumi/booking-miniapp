"""Command line.

booking-miniapp serve [--host 127.0.0.1] [--port 8080]   the Mini App server
booking-miniapp set-menu-button [--text "Записаться"]     put the Mini App button into the bot's chat
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from collections.abc import Sequence

from booking_miniapp import __version__
from booking_miniapp.config import Settings, load_settings


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="booking-miniapp", description="Telegram Mini App for booking-bot")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="run the Mini App server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8080)
    button = sub.add_parser("set-menu-button", help="show the Mini App as the menu button in the bot's chats")
    button.add_argument("--text", default="Записаться")
    return p


async def set_menu_button(settings: Settings, text: str, bot=None) -> None:
    from aiogram import Bot
    from aiogram.types import MenuButtonWebApp, WebAppInfo

    own = bot is None
    bot = bot or Bot(settings.bot_token)
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text=text, web_app=WebAppInfo(url=settings.webapp_url))
        )
    finally:
        if own:
            await bot.session.close()


def run(argv: Sequence[str] | None = None, settings: Settings | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = settings or load_settings()
    except (ValueError, RuntimeError) as exc:
        print(f"Ошибка настроек: {exc}", file=sys.stderr)
        return 2
    if args.command == "set-menu-button":
        if not settings.webapp_url:
            print("Задайте WEBAPP_URL (https://…) в .env", file=sys.stderr)
            return 2
        asyncio.run(set_menu_button(settings, args.text))
        print(f"Кнопка «{args.text}» → {settings.webapp_url}")
        return 0
    import uvicorn

    from booking_miniapp.api import create_app

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    uvicorn.run(create_app(settings), host=args.host, port=args.port, proxy_headers=True)
    return 0


def main() -> int:
    return run()
