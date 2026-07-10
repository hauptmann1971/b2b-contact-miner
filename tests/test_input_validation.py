"""Tests for input validation and security improvements in user routes."""
import importlib
import os
from unittest.mock import MagicMock, Mock, patch

import pytest

from models.database import Keyword, SessionLocal
from tests.conftest import get_csrf, login_session, post_add_keyword


class TestInputValidation:
  def test_empty_keyword_rejected(self, client):
    response = post_add_keyword(client, keyword="")
    assert response.status_code == 200
    response_text = response.data.decode("utf-8").lower()
    assert "пустым" in response_text or "error" in response_text

  def test_whitespace_only_keyword_rejected(self, client):
    response = post_add_keyword(client, keyword="   ")
    assert response.status_code == 200
    response_text = response.data.decode("utf-8").lower()
    assert "пустым" in response_text or "error" in response_text

  def test_very_long_keyword_rejected(self, client):
    response = post_add_keyword(client, keyword="a" * 501)
    assert response.status_code == 200
    response_text = response.data.decode("utf-8").lower()
    assert "слишком длинное" in response_text or "error" in response_text

  def test_max_length_keyword_accepted(self, client):
    response = post_add_keyword(client, keyword="a" * 500)
    assert response.status_code == 200
    response_text = response.data.decode("utf-8").lower()
    assert "слишком длинное" not in response_text

  def test_xss_characters_sanitized(self, client):
    login_session(client)
    csrf = get_csrf(client)
    xss_keyword = '<script>alert("xss")</script>test'
    client.post(
      "/add_keyword",
      data={"_csrf_token": csrf, "keyword": xss_keyword, "language": "ru", "country": "RU"},
      follow_redirects=True,
    )
    db = SessionLocal()
    try:
      row = db.query(Keyword).filter(Keyword.keyword.like("%test%")).order_by(Keyword.id.desc()).first()
      assert row is not None
      assert "<" not in row.keyword
      assert ">" not in row.keyword
      assert '"' not in row.keyword
      assert "'" not in row.keyword
    finally:
      db.close()

  def test_invalid_language_defaults_to_russian(self, client):
    login_session(client)
    csrf = get_csrf(client)
    client.post(
      "/add_keyword",
      data={"_csrf_token": csrf, "keyword": "test keyword", "language": "invalid_lang", "country": "RU"},
      follow_redirects=True,
    )
    db = SessionLocal()
    try:
      row = db.query(Keyword).filter(Keyword.keyword == "test keyword").first()
      assert row is not None
      assert row.language == "ru"
    finally:
      db.close()

  def test_invalid_country_defaults_to_russia(self, client):
    login_session(client)
    csrf = get_csrf(client)
    client.post(
      "/add_keyword",
      data={"_csrf_token": csrf, "keyword": "country test", "language": "ru", "country": "INVALID"},
      follow_redirects=True,
    )
    db = SessionLocal()
    try:
      row = db.query(Keyword).filter(Keyword.keyword == "country test").first()
      assert row is not None
      assert row.country == "RU"
    finally:
      db.close()

  def test_duplicate_keyword_rejected(self, client):
    post_add_keyword(client, keyword="existing keyword")
    response = post_add_keyword(client, keyword="existing keyword")
    response_text = response.data.decode("utf-8").lower()
    assert "уже существует" in response_text or "warning" in response_text

  def test_quotes_removed_from_keyword(self, client):
    login_session(client)
    csrf = get_csrf(client)
    client.post(
      "/add_keyword",
      data={"_csrf_token": csrf, "keyword": 'test "quoted" keyword', "language": "ru", "country": "RU"},
      follow_redirects=True,
    )
    db = SessionLocal()
    try:
      row = db.query(Keyword).filter(Keyword.keyword.like("%quoted%")).first()
      assert row is not None
      assert '"' not in row.keyword
      assert "'" not in row.keyword
    finally:
      db.close()


class TestSecretKeyGeneration:
  def test_secret_key_not_hardcoded(self, app):
    assert app.secret_key != "b2b-contact-miner-secret-key"

  def test_secret_key_is_generated(self):
    preserved = {
      key: os.environ[key]
      for key in ("DATABASE_URL", "SECRET_KEY")
      if key in os.environ
    }
    with patch.dict(os.environ, preserved, clear=True):
      import web_server

      importlib.reload(web_server)
      assert len(web_server.app.secret_key) == 64
      int(web_server.app.secret_key, 16)

  def test_secret_key_from_env(self):
    custom_key = "my-custom-secret-key-12345"
    with patch.dict(os.environ, {"SECRET_KEY": custom_key}):
      import web_server

      importlib.reload(web_server)
      assert web_server.app.secret_key == custom_key
