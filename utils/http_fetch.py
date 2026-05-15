"""Lightweight HTTP page fetch (before Playwright)."""
from __future__ import annotations

import re
from typing import Dict, Optional

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from config.settings import settings

_SCRIPT_STYLE_RE = re.compile(
    r"<(script|style|noscript)[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)


def html_to_text(html: str) -> str:
    """Strip tags and collapse whitespace for regex / JSON-LD extraction."""
    if not html:
        return ""
    try:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
    except Exception:
        text = _SCRIPT_STYLE_RE.sub(" ", html)
        text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


async def fetch_page_http(url: str, timeout_sec: Optional[float] = None) -> Optional[Dict[str, str]]:
    """
    Fetch URL via HTTP GET. Returns text/html dict or None on failure / empty body.
    """
    if not settings.HTTP_FETCH_ENABLED:
        return None

    timeout = timeout_sec if timeout_sec is not None else settings.HTTP_FETCH_TIMEOUT
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    }

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            verify=False,
            timeout=httpx.Timeout(timeout),
        ) as client:
            response = await client.get(url, headers=headers)
    except Exception as exc:
        logger.debug(f"HTTP fetch failed for {url}: {exc}")
        return None

    if response.status_code >= 400:
        logger.debug(f"HTTP {response.status_code} for {url}")
        return None

    html = (response.text or "").strip()
    if len(html) < 80:
        return None

    text = html_to_text(html)
    if len(text) < settings.HTTP_FETCH_MIN_TEXT_CHARS:
        logger.debug(
            f"HTTP body too short for {url}: {len(text)} chars "
            f"(min {settings.HTTP_FETCH_MIN_TEXT_CHARS})"
        )
        return None

    return {"text": text, "html": html, "status": str(response.status_code)}
