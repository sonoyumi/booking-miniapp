"""Checking who opened the Mini App.

Telegram passes the Mini App a string `initData` (user, auth_date, hash, ...) signed with a key
derived from the bot token. The browser sends it to us in `Authorization: tma <initData>`, and we
recompute the signature: only Telegram (and we, who know the token) can produce it, so a user
cannot pretend to be someone else by editing the request.

Algorithm (core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app):
    data_check_string = "\n".join(f"{key}={value}" for every field except hash, sorted by key)
    secret_key        = HMAC_SHA256(key="WebAppData", message=bot_token)
    hash              = hex(HMAC_SHA256(key=secret_key, message=data_check_string))
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode


class InitDataError(ValueError):
    pass


@dataclass(frozen=True)
class TgUser:
    id: int
    first_name: str
    last_name: str = ""
    username: str = ""
    language_code: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.username or str(self.id)


def _secret(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()


def sign(fields: dict[str, str], bot_token: str) -> str:
    """Builds a valid initData string. Used by tests and by nothing else."""
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    digest = hmac.new(_secret(bot_token), check.encode(), hashlib.sha256).hexdigest()
    return urlencode({**fields, "hash": digest})


def validate_init_data(init_data: str, bot_token: str, max_age: int, now: float | None = None) -> TgUser:
    if not init_data or len(init_data) > 4096:
        raise InitDataError("missing or too long init data")
    try:
        fields = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except ValueError:
        raise InitDataError("malformed init data") from None
    received = fields.pop("hash", "")
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    expected = hmac.new(_secret(bot_token), check.encode(), hashlib.sha256).hexdigest()
    if not received or not hmac.compare_digest(expected, received):  # constant time: no timing hints
        raise InitDataError("bad signature")

    try:
        auth_date = int(fields.get("auth_date", ""))
    except ValueError:
        raise InitDataError("no auth_date") from None
    age = (now if now is not None else time.time()) - auth_date
    if age > max_age or age < -300:  # stolen old strings expire; a little clock skew is fine
        raise InitDataError("init data expired, reopen the Mini App")

    try:
        user = json.loads(fields["user"])
        return TgUser(
            id=int(user["id"]),
            first_name=str(user.get("first_name", "")),
            last_name=str(user.get("last_name", "")),
            username=str(user.get("username", "")),
            language_code=str(user.get("language_code", "")),
        )
    except (KeyError, ValueError, TypeError):
        raise InitDataError("no user in init data") from None
