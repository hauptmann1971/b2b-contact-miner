"""Tests for admin settings, Telegram auth, and theme."""
import hashlib
import hmac
import time

import pytest

from tests.conftest import auth_header, login_session


def _telegram_payload(telegram_id: int = 42, bot_token: str = "123456:ABC-DEF") -> dict[str, str]:
    payload = {
        "id": str(telegram_id),
        "first_name": "Test",
        "username": "tester",
        "auth_date": str(int(time.time())),
    }
    check_string = "\n".join(f"{k}={payload[k]}" for k in sorted(payload))
    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    payload["hash"] = hmac.new(secret_key, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return payload


def _get_csrf(client):
    with client.session_transaction() as sess:
        if "_csrf_token" not in sess:
            client.get("/login")
        return sess.get("_csrf_token")


def test_login_page_shows_telegram_widget(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"telegram-widget.js" in response.data


def test_telegram_callback_sets_session(client):
    params = _telegram_payload()
    response = client.get("/login", query_string={**params, "next": "/user"}, follow_redirects=False)
    assert response.status_code == 302

    with client.session_transaction() as sess:
        assert sess.get("user_id")
        assert sess.get("tenant_id")


def test_password_form_login(client):
    response = login_session(client)
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get("auth_method") == "password"


def test_admin_access_after_login(client):
    login_session(client)
    response = client.get("/admin")
    assert response.status_code == 200
    assert b"Admin Console" in response.data or b"Admin Actions" in response.data or b"Recover Stale" in response.data


def test_admin_change_theme_route(client):
    login_session(client)
    csrf = _get_csrf(client)
    response = client.post(
        "/admin/settings/theme",
        data={"_csrf_token": csrf, "theme": "dark"},
        follow_redirects=True,
    )
    assert response.status_code == 200
