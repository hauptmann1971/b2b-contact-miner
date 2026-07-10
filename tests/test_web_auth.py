"""Tests for HTTP Basic auth on contacts and admin routes."""
import pytest

from tests.conftest import auth_header, login_session


def test_contacts_requires_auth(client):
    response = client.get("/contacts")
    assert response.status_code in (302, 401)


def test_contacts_rejects_wrong_password_without_500(client):
    response = client.get("/contacts", headers=auth_header("testadmin", "wrong"))
    assert response.status_code == 401


def test_contacts_allows_valid_auth(client):
    login_session(client)
    response = client.get("/contacts")
    assert response.status_code == 200


def test_admin_requires_auth(client):
    response = client.get("/admin")
    assert response.status_code == 200
    assert b"telegram-widget.js" in response.data or b"auth/login" in response.data


def test_api_stats_requires_auth(client):
    response = client.get("/api/stats")
    assert response.status_code in (302, 401)


def test_public_health_stays_open(client):
    response = client.get("/health")
    assert response.status_code in (200, 503)


def test_index_requires_login(client):
    response = client.get("/")
    assert response.status_code in (302, 401)
