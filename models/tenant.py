"""Multi-tenant users and organizations."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from models.database import Base

_COMMENT_ID = "Unique identifier"
_COMMENT_CREATED_AT = "Record creation timestamp"
_COMMENT_UPDATED_AT = "Last update timestamp"


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


WRITE_ROLES = frozenset({UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.MEMBER})
READ_ROLES = frozenset({UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.MEMBER, UserRole.VIEWER})
ADMIN_ROLES = frozenset({UserRole.SUPER_ADMIN, UserRole.OWNER})


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, autoincrement=True, comment=_COMMENT_ID)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    settings_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, comment=_COMMENT_CREATED_AT)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment=_COMMENT_UPDATED_AT)

    users = relationship("User", back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, comment=_COMMENT_ID)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    username = Column(String(128), nullable=False)
    password_hash = Column(String(255), nullable=True)
    telegram_id = Column(Integer, unique=True, nullable=True, index=True)
    display_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.MEMBER)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, comment=_COMMENT_CREATED_AT)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment=_COMMENT_UPDATED_AT)

    tenant = relationship("Tenant", back_populates="users")

    __table_args__ = (
        UniqueConstraint("tenant_id", "username", name="uq_users_tenant_username"),
        Index("idx_users_tenant_role", "tenant_id", "role"),
    )
