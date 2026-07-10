"""Request-scoped tenant context and query helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from flask import g, session
from sqlalchemy.orm import Query, Session

from models.tenant import ADMIN_ROLES, READ_ROLES, WRITE_ROLES, User, UserRole

T = TypeVar("T")


@dataclass(frozen=True)
class RequestContext:
    user_id: int
    tenant_id: int
    role: UserRole
    username: str
    display_name: str

    @property
    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN

    def can_read(self) -> bool:
        return self.role in READ_ROLES

    def can_write(self) -> bool:
        return self.role in WRITE_ROLES

    def can_admin(self) -> bool:
        return self.role in ADMIN_ROLES


def set_request_context(ctx: RequestContext | None) -> None:
    g.tenant_ctx = ctx


def get_request_context() -> RequestContext | None:
    return getattr(g, "tenant_ctx", None)


def get_request_context_or_raise() -> RequestContext:
    ctx = get_request_context()
    if ctx is None:
        raise RuntimeError("Tenant context is not set")
    return ctx


def load_context_from_session(db: Session) -> RequestContext | None:
    user_id = session.get("user_id")
    tenant_id = session.get("tenant_id")
    role_raw = session.get("role")
    if not user_id or not tenant_id or not role_raw:
        return None
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user or user.tenant_id != tenant_id:
        return None
    try:
        role = UserRole(role_raw)
    except ValueError:
        return None
    if user.role != role and user.role != UserRole.SUPER_ADMIN:
        role = user.role
    return RequestContext(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=role,
        username=user.username,
        display_name=user.display_name or user.username,
    )


def scoped_query(db: Session, model: type[T], ctx: RequestContext) -> Query:
    if ctx.is_super_admin:
        return db.query(model)
    if not hasattr(model, "tenant_id"):
        return db.query(model)
    return db.query(model).filter(model.tenant_id == ctx.tenant_id)


def keyword_belongs_to_tenant(db: Session, keyword_id: int, ctx: RequestContext) -> bool:
    from models.database import Keyword

    query = db.query(Keyword.id).filter(Keyword.id == keyword_id)
    if not ctx.is_super_admin:
        query = query.filter(Keyword.tenant_id == ctx.tenant_id)
    return query.first() is not None
