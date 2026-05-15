"""Serialize crawl page content for task_queue JSON payloads."""
from __future__ import annotations

from typing import Any, Dict, List

from config.settings import settings


def pack_crawl_content(content: List[Dict]) -> List[Dict]:
    """Trim page list for DB task payload (avoid huge JSON blobs)."""
    max_pages = settings.CRAWL_PAYLOAD_MAX_PAGES
    max_text = settings.CRAWL_PAYLOAD_MAX_TEXT_CHARS
    max_html = settings.CRAWL_PAYLOAD_MAX_HTML_CHARS
    packed: List[Dict] = []
    for item in (content or [])[:max_pages]:
        if not isinstance(item, dict):
            continue
        packed.append(
            {
                "url": item.get("url", ""),
                "content": (item.get("content") or "")[:max_text],
                "html": (item.get("html") or "")[:max_html],
                "type": item.get("type", "regular_page"),
                "priority": item.get("priority", 0),
            }
        )
    return packed


def unpack_crawl_content(raw: Any) -> List[Dict]:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    return []
