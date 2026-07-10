"""Tenant-scoped user management for admin UI."""
from __future__ import annotations

import re

from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from models.tenant import User, UserRole

MANAGEABLE_ROLES = (UserRole.VIEWER, UserRole.MEMBER, UserRole.OWNER)
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9._-]{3,128}$")


class UserAdminError(Exception):
    pass


def list_tenant_users(db: Session, tenant_id: int) -> list[User]:
    return db.query(User).filter(User.tenant_id == tenant_id).order_by(User.id.asc()).all()


def _count_owners(db: Session, tenant_id: int) -> int:
    return (
        db.query(User)
        .filter(User.tenant_id == tenant_id, User.role == UserRole.OWNER, User.is_active.is_(True))
        .count()
    )


def _get_tenant_user(db: Session, tenant_id: int, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
    if not user:
        raise UserAdminError("Пользователь не найден")
    return user


def _normalize_username(value: str) -> str:
    username = (value or "").strip().lower()
    if not _USERNAME_RE.fullmatch(username):
        raise UserAdminError("Логин: 3–128 символов, латиница, цифры, . _ -")
    return username


def _parse_role(value: str) -> UserRole:
    raw = (value or "").strip().lower()
    try:
        role = UserRole(raw)
    except ValueError as exc:
        raise UserAdminError("Недопустимая роль") from exc
    if role not in MANAGEABLE_ROLES:
        raise UserAdminError("Недопустимая роль")
    return role


def _ensure_not_last_owner(db: Session, user: User) -> None:
    if user.role == UserRole.OWNER and _count_owners(db, user.tenant_id) <= 1:
        raise UserAdminError("Нельзя изменить единственного owner в компании")


def create_tenant_user(
    db: Session,
    *,
    tenant_id: int,
    username: str,
    display_name: str,
    role: str,
    password: str | None = None,
    telegram_id: int | None = None,
) -> User:
    username = _normalize_username(username)
    role_enum = _parse_role(role)
    display_name = (display_name or username).strip() or username

    if db.query(User).filter(User.tenant_id == tenant_id, User.username == username).first():
        raise UserAdminError(f"Логин «{username}» уже занят")

    password = (password or "").strip()
    if telegram_id is None and not password:
        raise UserAdminError("Укажите пароль или Telegram ID")
    if password and len(password) < 8:
        raise UserAdminError("Пароль должен быть не короче 8 символов")

    if telegram_id is not None:
        conflict = db.query(User).filter(User.telegram_id == telegram_id).first()
        if conflict:
            raise UserAdminError("Этот Telegram ID уже привязан к другому пользователю")

    user = User(
        tenant_id=tenant_id,
        username=username,
        password_hash=generate_password_hash(password) if password else None,
        telegram_id=telegram_id,
        display_name=display_name,
        role=role_enum,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_role(
    db: Session,
    *,
    tenant_id: int,
    user_id: int,
    role: str,
    actor_user_id: int,
) -> User:
    user = _get_tenant_user(db, tenant_id, user_id)
    new_role = _parse_role(role)
    if user.id == actor_user_id and user.role == UserRole.OWNER and new_role != UserRole.OWNER:
        _ensure_not_last_owner(db, user)
    if user.role == UserRole.OWNER and new_role != UserRole.OWNER:
        _ensure_not_last_owner(db, user)
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user


def set_user_active(
    db: Session,
    *,
    tenant_id: int,
    user_id: int,
    is_active: bool,
    actor_user_id: int,
) -> User:
    user = _get_tenant_user(db, tenant_id, user_id)
    if user.id == actor_user_id and not is_active:
        raise UserAdminError("Нельзя деактивировать свой аккаунт")
    if not is_active and user.role == UserRole.OWNER:
        _ensure_not_last_owner(db, user)
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def set_user_password(
    db: Session,
    *,
    tenant_id: int,
    user_id: int,
    password: str,
) -> User:
    user = _get_tenant_user(db, tenant_id, user_id)
    password = (password or "").strip()
    if len(password) < 8:
        raise UserAdminError("Пароль должен быть не короче 8 символов")
    user.password_hash = generate_password_hash(password)
    db.commit()
    db.refresh(user)
    return user
