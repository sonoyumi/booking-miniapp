import hashlib
import hmac
import json
from urllib.parse import parse_qsl, urlencode

import pytest
from conftest import ANNA, NOW, TOKEN

from booking_miniapp.auth import InitDataError, sign, validate_init_data

FIELDS = {"auth_date": str(int(NOW.timestamp())), "query_id": "AAH", "user": json.dumps(ANNA)}


NOW_TS = NOW.timestamp()


def check(init_data: str, now=NOW_TS, token=TOKEN):
    return validate_init_data(init_data, token, max_age=86_400, now=now)


def test_signature_matches_telegram_algorithm_computed_by_hand():
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(FIELDS.items()))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    assert dict(parse_qsl(sign(FIELDS, TOKEN)))["hash"] == expected


def test_valid_login():
    user = check(sign(FIELDS, TOKEN))
    assert (user.id, user.full_name, user.username) == (100, "Anna Rossi", "anna")


def test_any_change_breaks_the_signature():
    fields = dict(parse_qsl(sign(FIELDS, TOKEN)))
    fields["user"] = json.dumps({**ANNA, "id": 999})  # pretend to be someone else
    with pytest.raises(InitDataError, match="bad signature"):
        check(urlencode(fields))
    with pytest.raises(InitDataError, match="bad signature"):
        check(sign(FIELDS, "other:token"))  # signed for another bot


def test_old_login_expires_and_future_is_rejected():
    with pytest.raises(InitDataError, match="expired"):
        check(sign(FIELDS, TOKEN), now=NOW_TS + 86_401)
    with pytest.raises(InitDataError, match="expired"):
        check(sign(FIELDS, TOKEN), now=NOW_TS - 3600)


@pytest.mark.parametrize("raw", ["", "no-equals-sign", "a=1&hash=", "x" * 5000])
def test_garbage(raw):
    with pytest.raises(InitDataError):
        check(raw)


def test_signed_but_without_user():
    with pytest.raises(InitDataError, match="no user"):
        check(sign({"auth_date": FIELDS["auth_date"]}, TOKEN))
