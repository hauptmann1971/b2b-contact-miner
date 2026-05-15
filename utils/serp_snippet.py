"""Extract contacts from SERP title/snippet before crawl."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from models.schemas import ContactInfo
from services.extraction_service import ExtractionService

_extractor: Optional[ExtractionService] = None


def _get_extractor() -> ExtractionService:
    global _extractor
    if _extractor is None:
        _extractor = ExtractionService()
    return _extractor


def serp_text_blob(title: Optional[str], snippet: Optional[str]) -> str:
    parts = [(title or "").strip(), (snippet or "").strip()]
    return "\n".join(p for p in parts if p)


def build_snippet_content_item(
    url: str,
    title: Optional[str],
    snippet: Optional[str],
) -> Dict:
    """Synthetic crawl item for extraction_service."""
    blob = serp_text_blob(title, snippet)
    return {
        "url": url or "serp://snippet",
        "content": blob,
        "html": "",
        "type": "serp_snippet",
        "priority": 10,
    }


def snippet_has_actionable_contacts(title: Optional[str], snippet: Optional[str]) -> bool:
    """True when SERP text likely contains email or Telegram (skip crawl)."""
    contacts, _ = extract_serp_snippet_contacts("https://snippet.local/", title, snippet)
    return bool(contacts.emails or contacts.telegram_links)


def extract_serp_snippet_contacts(
    url: str,
    title: Optional[str],
    snippet: Optional[str],
) -> Tuple[ContactInfo, Optional[dict]]:
    blob = serp_text_blob(title, snippet)
    if not blob.strip():
        return ContactInfo(), None
    item = build_snippet_content_item(url, title, snippet)
    return _get_extractor().extract_contacts([item])
