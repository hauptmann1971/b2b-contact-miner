"""Tenant isolation tests."""
import uuid

from models.database import Keyword, SessionLocal
from models.tenant import Tenant, User, UserRole
from services.tenant_bootstrap import bootstrap_default_tenant, ensure_multitenant_schema
from werkzeug.security import generate_password_hash


def test_keyword_unique_per_tenant():
    ensure_multitenant_schema()
    bootstrap_default_tenant()
    suffix = uuid.uuid4().hex[:8]
    term = f"shared-term-{suffix}"
    db = SessionLocal()
    try:
        tenant_b = Tenant(slug=f"tenant-b-{suffix}", name="Tenant B", is_active=True)
        db.add(tenant_b)
        db.flush()
        db.add(
            User(
                tenant_id=tenant_b.id,
                username=f"userb-{suffix}",
                password_hash=generate_password_hash("passwordb"),
                role=UserRole.OWNER,
                is_active=True,
            )
        )
        default_tenant = db.query(Tenant).filter(Tenant.slug == "test-company").first() or db.query(Tenant).first()
        db.add(Keyword(tenant_id=default_tenant.id, keyword=term, language="ru", country="RU"))
        db.add(Keyword(tenant_id=tenant_b.id, keyword=term, language="ru", country="RU"))
        db.commit()
        count = db.query(Keyword).filter(Keyword.keyword == term).count()
        assert count == 2
    finally:
        db.close()
