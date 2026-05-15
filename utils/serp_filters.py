"""SERP result filtering and query building (provider-agnostic)."""
from __future__ import annotations

from typing import Dict, List, Set, Tuple
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
    "netguru.com",
    "munich-startup.de",
    "blockchain.com",
    "learn.bybit.com",
)

# URL path scoring for pick_urls_for_crawl (higher = crawl first / prefer per host).
_HIGH_CONTACT_MARKERS = (
    "/contact", "/contacts", "/contact-us", "/kontakt", "/impressum", "/reach-us",
)
_MEDIUM_CONTACT_MARKERS = (
    "/about", "/about-us", "/team", "/our-team", "/leadership", "/company", "/who-we-are",
)
_LOW_VALUE_MARKERS = (
    "/blog", "/news", "/press", "/article", "/post/", "/tag/", "/category/", "/stories/",
)
_SKIP_PATH_EXTENSIONS = (
    ".pdf", ".zip", ".doc", ".docx", ".xls", ".xlsx", ".mp4", ".jpg", ".jpeg", ".png", ".gif",
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


def score_crawl_url(url: str) -> int:
    """
    Score SERP URL for crawl priority. Higher is better.
    PDF/archives and similar paths return a large negative score (skip).
    """
    path = (urlparse(url).path or "").lower()
    if any(path.endswith(ext) for ext in _SKIP_PATH_EXTENSIONS):
        return -1000

    score = 0
    for marker in _HIGH_CONTACT_MARKERS:
        if marker in path:
            score += 100
    for marker in _MEDIUM_CONTACT_MARKERS:
        if marker in path:
            score += 60
    for marker in _LOW_VALUE_MARKERS:
        if marker in path:
            score -= 45

    stripped = path.rstrip("/")
    if stripped in ("", ""):
        score += 25

    segments = [s for s in path.split("/") if s]
    if len(segments) >= 4 and score < 60:
        score -= 15

    return score


def pick_urls_for_crawl(results: List[Dict]) -> List[str]:
    """
    Dedupe by host; keep highest-scored URL per host; order hosts by score descending.
    Article-like SERP URLs also consider domain root as a fallback candidate.
    """
    host_best: Dict[str, Tuple[int, str]] = {}

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
            if is_blocked_url(candidate):
                continue
            crawl_score = score_crawl_url(candidate)
            if crawl_score <= -1000:
                continue
            h = normalize_host(candidate)
            prev = host_best.get(h)
            if prev is None or crawl_score > prev[0]:
                host_best[h] = (crawl_score, candidate)

    ranked = sorted(host_best.values(), key=lambda item: item[0], reverse=True)
    return [url for _, url in ranked]
