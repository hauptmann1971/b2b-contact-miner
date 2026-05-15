"""SERP result filtering and query building (provider-agnostic)."""
from __future__ import annotations

from typing import Dict, List, Set
from urllib.parse import urlparse

from config.settings import settings

# Domains that rarely yield B2B contacts worth crawling.
DEFAULT_BLOCKED_HOST_SUFFIXES = (
    "wikipedia.org",
    "wikimedia.org",
    "reddit.com",
    "quora.com",
    "stackoverflow.com",
    "youtube.com",
    "youtu.be",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "tiktok.com",
    "pinterest.com",
    "amazon.com",
    "amazon.de",
    "ebay.com",
    "google.com",
    "google.ru",
    "yandex.ru",
    "ya.ru",
    "bing.com",
    "chatgpt.com",
    "openai.com",
    "gemini.google.com",
    "grokipedia.com",
    "gabler-banklexikon.de",
    "investopedia.com",
    "britannica.com",
    "medium.com",
    "forbes.com",
    "crunchbase.com",
    "bloomberg.com",
    "techcrunch.com",
)


def normalize_host(url: str) -> str:
    """Return lowercase hostname without www."""
    try:
        host = (urlparse(url).netloc or "").lower()
    except Exception:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def is_blocked_url(url: str) -> bool:
    """True if URL should not be crawled (aggregators, social, encyclopedia)."""
    host = normalize_host(url)
    if not host:
        return True
    blocked = set(settings.SERP_BLOCKED_HOST_SUFFIXES or DEFAULT_BLOCKED_HOST_SUFFIXES)
    for suffix in blocked:
        s = suffix.lower().lstrip(".")
        if host == s or host.endswith("." + s):
            return True
    return False


def build_search_query(keyword: str, language: str = "ru", country: str = "RU") -> str:
    """Build a provider-agnostic B2B-oriented search query (no invalid site:COUNTRY)."""
    kw = (keyword or "").strip()
    if not kw:
        return ""
    # Light locale hint without breaking DuckDuckGo / Google adapters.
    if language == "de" or country == "DE":
        return f'{kw} kontakt impressum'
    if language == "en" or country in ("US", "GB"):
        return f'{kw} contact email'
    return f'{kw} контакты email'


def filter_search_results(results: List[Dict]) -> List[Dict]:
    """Drop blocked hosts and empty URLs; preserve order."""
    filtered: List[Dict] = []
    for item in results:
        url = (item.get("url") or "").strip()
        if not url or is_blocked_url(url):
            continue
        filtered.append(item)
    return filtered


def _root_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        return f"https://{parsed.netloc}/" if parsed.netloc else f"https://{url.strip('/')}/"
    return f"{parsed.scheme}://{parsed.netloc}/"


def _needs_domain_fallback(url: str) -> bool:
    path = (urlparse(url).path or "").lower()
    markers = ["/news/", "/article", "/press", "/blog/", "/post/", ".html", ".htm"]
    return len(path) > 1 and any(m in path for m in markers)


def pick_urls_for_crawl(results: List[Dict]) -> List[str]:
    """
    Dedupe by registrable host; prefer article URL + root when article-like.
    Returns unique crawl candidate URLs in priority order.
    """
    seen_hosts: Set[str] = set()
    urls: List[str] = []

    for result in results:
        url = (result.get("url") or "").strip()
        if not url or is_blocked_url(url):
            continue
        host = normalize_host(url)
        if not host:
            continue

        candidates = [url]
        if _needs_domain_fallback(url):
            root = _root_url(url)
            if normalize_host(root) == host and root not in candidates:
                candidates.append(root)

        for candidate in candidates:
            h = normalize_host(candidate)
            if h in seen_hosts:
                continue
            seen_hosts.add(h)
            urls.append(candidate)

    return urls
