"""Tests for admin user management page."""
import uuid

from models.database import SessionLocal
from models.tenant import User
from tests.conftest import get_csrf, login_session


def test_admin_users_requires_owner(client):
    login_session(client)
    response = client.get("/admin/users")
    assert response.status_code == 200
    assert b"admin_users" in response.data or "Пользователи".encode("utf-8") in response.data or b"testadmin" in response.data


def test_admin_users_create_member(client):
    login_session(client)
    csrf = get_csrf(client)
    username = f"colleague_{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/admin/users/create",
        data={
            "_csrf_token": csrf,
            "username": username,
            "display_name": "Colleague",
            "role": "member",
            "password": "ColleaguePass1",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        assert user is not None
        assert user.role.value == "member"
        assert user.is_active is True
    finally:
        db.close()


def test_admin_users_page_lists_users(client):
    login_session(client)
    response = client.get("/admin/users")
    assert response.status_code == 200
    assert b"testadmin" in response.data or b"admin" in response.data
