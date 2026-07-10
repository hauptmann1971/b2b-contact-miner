"""Telegram Login Widget verification."""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any


def telegram_auth_configured() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip() and os.getenv("TELEGRAM_BOT_USERNAME", "").strip())


def get_bot_username() -> str:
    return os.getenv("TELEGRAM_BOT_USERNAME", "").strip()


def verify_telegram_login(data: dict[str, Any], max_age_seconds: int = 86400) -> bool:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        return False

    payload = {k: str(v) for k, v in data.items() if k != "hash" and v is not None}
    received_hash = str(data.get("hash", "")).strip()
    if not received_hash:
        return False

    try:
        auth_date = int(payload.get("auth_date", "0"))
    except ValueError:
        return False
    if auth_date <= 0 or time.time() - auth_date > max_age_seconds:
        return False

    check_string = "\n".join(f"{k}={payload[k]}" for k in sorted(payload))
    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    computed_hash = hmac.new(secret_key, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed_hash, received_hash)
