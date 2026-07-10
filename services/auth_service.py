"""User authentication against tenants/users tables."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash

from models.tenant import User


def authenticate_password(db: Session, username: str, password: str) -> User | None:
    username = (username or "").strip()
    if not username or not password:
        return None
    user = (
        db.query(User)
        .filter(User.username == username, User.is_active.is_(True))
        .order_by(User.id.asc())
        .first()
    )
    if not user or not user.password_hash:
        return None
    if not check_password_hash(user.password_hash, password):
        return None
    user.last_login_at = datetime.utcnow()
    db.commit()
    return user


def find_user_by_telegram_id(db: Session, telegram_id: int) -> User | None:
    user = db.query(User).filter(User.telegram_id == telegram_id, User.is_active.is_(True)).first()
    if user:
        user.last_login_at = datetime.utcnow()
        db.commit()
    return user


def verify_basic_user(db: Session, username: str | None, password: str | None) -> User | None:
    return authenticate_password(db, username or "", password or "")
