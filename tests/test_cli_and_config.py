import pytest
from conftest import TOKEN

from booking_miniapp import cli
from booking_miniapp.config import load_settings

NAMES = (
    "BOT_TOKEN",
    "ADMIN_IDS",
    "TIMEZONE",
    "WORK_START",
    "WORK_END",
    "SLOT_MINUTES",
    "DAYS_AHEAD",
    "WORK_DAYS",
    "DATABASE_PATH",
    "SERVICES_PATH",
    "SHOP_NAME",
    "WEBAPP_URL",
    "INIT_DATA_MAX_AGE",
    "MAX_ACTIVE_PER_USER",
    "DEV_USER_ID",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in NAMES:
        monkeypatch.setenv(name, "")
    monkeypatch.setenv("BOT_TOKEN", TOKEN)


def test_defaults_match_booking_bot():
    s = load_settings(env_file=None)
    assert s.schedule.work_start == 10 and s.schedule.work_end == 19 and s.schedule.work_days == {1, 2, 3, 4, 5, 6}
    assert str(s.database_path) == "data/bookings.db" and TOKEN not in repr(s) and s.dev_user_id is None


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("BOT_TOKEN", "", "BOT_TOKEN"),
        ("TIMEZONE", "Mars/Base", "TIMEZONE"),
        ("WEBAPP_URL", "http://x.it", "https://"),
        ("WORK_START", "ten", "WORK_START"),
    ],
)
def test_bad_settings(monkeypatch, name, value, message):
    monkeypatch.setenv(name, value)
    with pytest.raises((ValueError, RuntimeError), match=message):
        load_settings(env_file=None)


async def test_menu_button(settings):
    calls = []

    class FakeBot:
        async def set_chat_menu_button(self, menu_button):
            calls.append(menu_button)

    s = settings.__class__(**{**settings.__dict__, "webapp_url": "https://book.example.it"})
    await cli.set_menu_button(s, "Prenota", bot=FakeBot())
    assert calls[0].text == "Prenota" and calls[0].web_app.url == "https://book.example.it"


def test_cli_needs_webapp_url(settings, capsys):
    assert cli.run(["set-menu-button"], settings=settings) == 2
    assert "WEBAPP_URL" in capsys.readouterr().err
