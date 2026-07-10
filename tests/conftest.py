import os

import pytest
from werkzeug.security import generate_password_hash


def _ensure_test_owner() -> None:
    """Guarantee testadmin owner for pytest even when prod owner already exists."""
    from models.database import SessionLocal
    from models.tenant import Tenant, User, UserRole

    db = SessionLocal()
    try:
        slug = os.getenv("DEFAULT_TENANT_SLUG", "test-company").strip() or "test-company"
        tenant = db.query(Tenant).filter(Tenant.slug == slug).first()
        if not tenant:
            tenant = db.query(Tenant).order_by(Tenant.id.asc()).first()
        if not tenant:
            tenant = Tenant(slug=slug, name="Test Company", is_active=True)
            db.add(tenant)
            db.flush()

        user = db.query(User).filter(User.tenant_id == tenant.id, User.username == "testadmin").first()
        if not user:
            user = User(tenant_id=tenant.id, username="testadmin", is_active=True)
            db.add(user)
        user.password_hash = generate_password_hash("testpass")
        user.role = UserRole.OWNER
        user.telegram_id = 42
        user.display_name = "Test Admin"
        user.is_active = True
        db.commit()
    finally:
        db.close()


@pytest.fixture(scope="session")
def _db_ready():
    from services.tenant_bootstrap import bootstrap_default_tenant, ensure_multitenant_schema

    ensure_multitenant_schema()
    bootstrap_default_tenant()
    yield


@pytest.fixture
def app(monkeypatch, tmp_path, _db_ready):
    settings_file = tmp_path / "app_settings.json"
    monkeypatch.setenv("APP_SETTINGS_PATH", str(settings_file))
    monkeypatch.setenv("ADMIN_USERNAME", "testadmin")
    monkeypatch.setenv("ADMIN_PASSWORD", "testpass")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF")
    monkeypatch.setenv("TELEGRAM_BOT_USERNAME", "test_bot")
    monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "42")
    monkeypatch.setenv("DEFAULT_TENANT_SLUG", "company")
    monkeypatch.setenv("DEFAULT_TENANT_NAME", "Company")

    _ensure_test_owner()

    from web_server import app as flask_app

    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def auth_header(username: str, password: str) -> dict[str, str]:
    import base64

    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def login_session(client, username: str = "testadmin", password: str = "testpass"):
    with client.session_transaction() as sess:
        if "_csrf_token" not in sess:
            client.get("/login")
        csrf = sess.get("_csrf_token")
    return client.post(
        "/auth/login",
        data={"_csrf_token": csrf, "username": username, "password": password, "next": "/user"},
        follow_redirects=True,
    )


def get_csrf(client) -> str:
    with client.session_transaction() as sess:
        if "_csrf_token" not in sess:
            client.get("/login")
        return sess.get("_csrf_token")


def post_add_keyword(client, **form_fields):
    login_session(client)
    csrf = get_csrf(client)
    data = {"_csrf_token": csrf, "language": "ru", "country": "RU", **form_fields}
    return client.post("/add_keyword", data=data, follow_redirects=True)
