"""Persistent app settings (admin password hash, default theme)."""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

_LOCK = threading.Lock()
_VALID_THEMES = frozenset({"light", "dark"})


def _settings_path() -> Path:
    return Path(os.getenv("APP_SETTINGS_PATH", "data/app_settings.json"))


def _default_settings() -> dict[str, Any]:
    return {"username": "", "password_hash": "", "default_theme": "light"}


def _ensure_parent() -> None:
    _settings_path().parent.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict[str, Any]:
    path = _settings_path()
    if not path.exists():
        return _default_settings()
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return _default_settings()
    merged = _default_settings()
    merged.update({k: v for k, v in data.items() if k in merged})
    if merged["default_theme"] not in _VALID_THEMES:
        merged["default_theme"] = "light"
    return merged


def save_settings(settings: dict[str, Any]) -> None:
    payload = _default_settings()
    payload.update({k: settings.get(k, payload[k]) for k in payload})
    if payload["default_theme"] not in _VALID_THEMES:
        payload["default_theme"] = "light"
    with _LOCK:
        _ensure_parent()
        path = _settings_path()
        tmp = path.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        tmp.replace(path)


def get_stored_admin_credentials() -> tuple[str, str] | None:
    settings = load_settings()
    username = (settings.get("username") or "").strip()
    password_hash = (settings.get("password_hash") or "").strip()
    if username and password_hash:
        return username, password_hash
    return None


def get_admin_username() -> str:
    stored = get_stored_admin_credentials()
    if stored:
        return stored[0]
    return os.getenv("ADMIN_USERNAME", "").strip()


def verify_admin_password(username: str | None, password: str | None) -> bool:
    stored = get_stored_admin_credentials()
    if stored:
        expected_user, password_hash = stored
        if (username or "").strip() != expected_user:
            return False
        return check_password_hash(password_hash, password or "")
    expected_user = os.getenv("ADMIN_USERNAME", "").strip()
    expected_password = os.getenv("ADMIN_PASSWORD", "")
    from utils.basic_auth import _secure_str_eq

    return _secure_str_eq(username, expected_user) and _secure_str_eq(password, expected_password)


def change_admin_password(current_password: str, new_password: str) -> tuple[bool, str]:
    username = get_admin_username()
    if not username:
        return False, "Admin username is not configured"
    if not verify_admin_password(username, current_password):
        return False, "Current password is incorrect"
    if len(new_password) < 8:
        return False, "New password must be at least 8 characters"
    settings = load_settings()
    settings["username"] = username
    settings["password_hash"] = generate_password_hash(new_password)
    save_settings(settings)
    return True, "Password updated"


def get_default_theme() -> str:
    theme = load_settings().get("default_theme", "light")
    return theme if theme in _VALID_THEMES else "light"


def set_default_theme(theme: str) -> tuple[bool, str]:
    if theme not in _VALID_THEMES:
        return False, "Unknown theme"
    settings = load_settings()
    settings["default_theme"] = theme
    save_settings(settings)
    return True, "Theme updated"
