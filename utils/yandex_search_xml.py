"""Parse Yandex Search API v2 XML payload (rawData)."""
from __future__ import annotations

import base64
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List


def decode_raw_data(raw: Any) -> str:
    """Accept base64 string or bytes from API JSON field rawData."""
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace")
    text = str(raw).strip()
    if not text:
        return ""
    if text.startswith("<"):
        return text
    try:
        return base64.b64decode(text).decode("utf-8", errors="replace")
    except Exception:
        return text


def _local(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def parse_web_search_xml(xml_text: str, max_results: int = 10) -> List[Dict]:
    """
    Extract url, title, snippet from Yandex Search XML.
    Returns list of {url, title, snippet, position}.
    """
    if not xml_text or not xml_text.strip():
        return []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    results: List[Dict] = []
    position = 0

    for elem in root.iter():
        if _local(elem.tag) != "doc":
            continue
        url = ""
        title = ""
        snippets: List[str] = []
        for child in elem:
            tag = _local(child.tag)
            if tag == "url" and child.text:
                url = child.text.strip()
            elif tag == "title" and child.text:
                title = child.text.strip()
            elif tag == "passage" and child.text:
                snippets.append(child.text.strip())
            elif tag == "passages":
                for passage in child:
                    if _local(passage.tag) == "passage" and passage.text:
                        snippets.append(passage.text.strip())
            elif tag == "headline" and child.text and not title:
                title = child.text.strip()

        if not url:
            continue
        position += 1
        snippet = " ".join(snippets[:3]).strip()
        if len(snippet) > 500:
            snippet = snippet[:500] + "…"
        results.append({
            "url": url,
            "title": title,
            "snippet": snippet,
            "position": position,
        })
        if len(results) >= max_results:
            break

    return results


def parse_api_response_body(data: dict, max_results: int = 10) -> List[Dict]:
    """Parse REST JSON body with rawData field."""
    raw = data.get("rawData") or data.get("raw_data")
    xml_text = decode_raw_data(raw)
    if not xml_text and isinstance(data.get("error"), dict):
        raise ValueError(data["error"].get("message", str(data["error"])))
    return parse_web_search_xml(xml_text, max_results=max_results)
