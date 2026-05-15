import pytest

from utils.http_fetch import html_to_text


def test_html_to_text_strips_scripts():
    html = "<html><body><script>alert(1)</script><p>Hello contact@test.co</p></body></html>"
    text = html_to_text(html)
    assert "alert" not in text
    assert "contact@test.co" in text


@pytest.mark.asyncio
async def test_fetch_page_http_disabled(monkeypatch):
    from config import settings as settings_mod
    from utils import http_fetch

    monkeypatch.setattr(settings_mod.settings, "HTTP_FETCH_ENABLED", False)
    out = await http_fetch.fetch_page_http("https://example.com")
    assert out is None
