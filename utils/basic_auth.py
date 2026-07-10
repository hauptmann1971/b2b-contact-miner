"""Shared HTTP Basic auth helpers for Flask and FastAPI."""
from __future__ import annotations

from models.database import SessionLocal
from services.auth_service import verify_basic_user


def verify_basic_auth(username: str | None, password: str | None) -> bool:
    db = SessionLocal()
    try:
        return verify_basic_user(db, username, password) is not None
    finally:
        db.close()


def admin_credentials_configured() -> bool:
    db = SessionLocal()
    try:
        from models.tenant import User

        return db.query(User).filter(User.is_active.is_(True)).count() > 0
    finally:
        db.close()
