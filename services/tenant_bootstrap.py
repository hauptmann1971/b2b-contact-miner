"""Bootstrap default tenant/users and backfill tenant_id."""
from __future__ import annotations

import os

from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash

from models.database import SessionLocal, engine
from models.tenant import Tenant, User, UserRole


def _table_exists(table_name: str) -> bool:
    return inspect(engine).has_table(table_name)


def _column_exists(table_name: str, column_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    cols = {col["name"] for col in inspect(engine).get_columns(table_name)}
    return column_name in cols


def ensure_multitenant_schema() -> None:
    from models.database import Base
    import models.tenant  # noqa: F401
    import models.task_queue  # noqa: F401 — register task_queue for create_all

    Base.metadata.create_all(bind=engine)
    _add_tenant_columns_if_missing()
    _migrate_keyword_indexes()


def _index_names(table_name: str) -> set[str]:
    if not _table_exists(table_name):
        return set()
    return {idx["name"] for idx in inspect(engine).get_indexes(table_name)}


def _migrate_keyword_indexes() -> None:
    if not _table_exists("keywords"):
        return
    legacy_indexes = {"ix_keywords_keyword", "keyword"}
    with engine.begin() as conn:
        for idx in inspect(engine).get_indexes("keywords"):
            name = idx["name"]
            column_names = idx.get("column_names") or []
            if name in legacy_indexes or (idx.get("unique") and column_names == ["keyword"]):
                conn.execute(text(f"ALTER TABLE keywords DROP INDEX `{name}`"))
        if "idx_keywords_tenant_keyword" not in _index_names("keywords"):
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX idx_keywords_tenant_keyword "
                    "ON keywords (tenant_id, keyword, language, country)"
                )
            )


def _add_tenant_columns_if_missing() -> None:
    ddl = [
        ("keywords", "tenant_id", "INT NULL"),
        ("keywords", "created_by_user_id", "INT NULL"),
        ("search_results", "tenant_id", "INT NULL"),
        ("domain_contacts", "tenant_id", "INT NULL"),
        ("contacts", "tenant_id", "INT NULL"),
        ("pipeline_state", "tenant_id", "INT NULL"),
        ("crawl_logs", "tenant_id", "INT NULL"),
        ("task_queue", "tenant_id", "INT NULL"),
    ]
    with engine.begin() as conn:
        for table, column, col_type in ddl:
            if _table_exists(table) and not _column_exists(table, column):
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))


def bootstrap_default_tenant(db=None) -> Tenant:
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        tenant = db.query(Tenant).order_by(Tenant.id.asc()).first()
        if not tenant:
            slug = os.getenv("DEFAULT_TENANT_SLUG", "company").strip() or "company"
            name = os.getenv("DEFAULT_TENANT_NAME", "Company").strip() or "Company"
            tenant = Tenant(slug=slug, name=name, is_active=True)
            db.add(tenant)
            db.commit()
            db.refresh(tenant)

        _ensure_owner_user(db, tenant)
        _backfill_tenant_ids(db, tenant.id)
        db.commit()
        return tenant
    finally:
        if close_db:
            db.close()


def _ensure_owner_user(db, tenant: Tenant) -> User:
    owner = db.query(User).filter(User.tenant_id == tenant.id, User.role == UserRole.OWNER).first()
    if owner:
        return owner

    username = os.getenv("ADMIN_USERNAME", "admin").strip() or "admin"
    password = os.getenv("ADMIN_PASSWORD", "").strip()
    telegram_raw = os.getenv("ADMIN_TELEGRAM_IDS", "").strip()
    telegram_id = int(telegram_raw.split(",")[0]) if telegram_raw.split(",")[0].isdigit() else None

    existing = db.query(User).filter(User.tenant_id == tenant.id, User.username == username).first()
    if existing:
        if telegram_id and not existing.telegram_id:
            existing.telegram_id = telegram_id
        if password and not existing.password_hash:
            existing.password_hash = generate_password_hash(password)
        existing.role = UserRole.OWNER
        return existing

    user = User(
        tenant_id=tenant.id,
        username=username,
        password_hash=generate_password_hash(password) if password else None,
        telegram_id=telegram_id,
        display_name=username,
        role=UserRole.OWNER,
        is_active=True,
    )
    db.add(user)
    db.flush()

    for part in [p.strip() for p in telegram_raw.split(",") if p.strip()]:
        if not part.isdigit() or int(part) == telegram_id:
            continue
        if db.query(User).filter(User.telegram_id == int(part)).first():
            continue
        db.add(
            User(
                tenant_id=tenant.id,
                username=f"tg_{part}",
                telegram_id=int(part),
                display_name=f"Telegram {part}",
                role=UserRole.MEMBER,
                is_active=True,
            )
        )
    return user


def _backfill_tenant_ids(db, tenant_id: int) -> None:
    statements = [
        "UPDATE keywords SET tenant_id = :tid WHERE tenant_id IS NULL",
        "UPDATE search_results sr JOIN keywords k ON k.id = sr.keyword_id SET sr.tenant_id = k.tenant_id WHERE sr.tenant_id IS NULL",
        "UPDATE domain_contacts dc JOIN search_results sr ON sr.id = dc.search_result_id SET dc.tenant_id = sr.tenant_id WHERE dc.tenant_id IS NULL",
        "UPDATE contacts c JOIN domain_contacts dc ON dc.id = c.domain_contact_id SET c.tenant_id = dc.tenant_id WHERE c.tenant_id IS NULL",
        "UPDATE pipeline_state ps LEFT JOIN keywords k ON k.id = ps.keyword_id SET ps.tenant_id = COALESCE(k.tenant_id, :tid) WHERE ps.tenant_id IS NULL",
        "UPDATE crawl_logs SET tenant_id = :tid WHERE tenant_id IS NULL",
    ]
    if _table_exists("task_queue"):
        statements.append(
            "UPDATE task_queue tq LEFT JOIN keywords k ON k.id = tq.keyword_id "
            "SET tq.tenant_id = COALESCE(k.tenant_id, :tid) WHERE tq.tenant_id IS NULL"
        )
    for sql in statements:
        db.execute(text(sql), {"tid": tenant_id})
