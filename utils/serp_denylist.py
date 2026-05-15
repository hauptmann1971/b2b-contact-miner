"""Suggest SERP host suffixes to block based on zero-page crawl history."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Set, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from config.settings import settings
from models.database import CrawlLog, DomainContact
from utils.serp_constants import DEFAULT_BLOCKED_HOST_SUFFIXES
from utils.serp_filters import normalize_host


def suggest_blocked_hosts(
    db: Session,
    *,
    days: int | None = None,
    min_zero_crawls: int | None = None,
    limit: int = 25,
) -> List[Tuple[str, int, str]]:
    """
    Hosts with repeated zero-page crawls and no saved domain_contacts.

    Returns list of (host_suffix, zero_count, reason).
    """
    days = days if days is not None else settings.SERP_DENYLIST_LOOKBACK_DAYS
    min_zero = min_zero_crawls if min_zero_crawls is not None else settings.SERP_DENYLIST_MIN_ZERO_CRAWLS
    since = datetime.now(timezone.utc) - timedelta(days=days)

    zero_rows = (
        db.query(CrawlLog.domain, func.count(CrawlLog.id))
        .filter(CrawlLog.crawled_at >= since, CrawlLog.pages_crawled == 0)
        .group_by(CrawlLog.domain)
        .having(func.count(CrawlLog.id) >= min_zero)
        .order_by(func.count(CrawlLog.id).desc())
        .limit(limit * 3)
        .all()
    )

    contact_hosts: Set[str] = set()
    for (domain,) in db.query(DomainContact.domain).distinct().all():
        host = normalize_host(f"https://{domain}/" if domain and "://" not in domain else domain)
        if host:
            contact_hosts.add(host)

    try:
        blocked = set(settings.SERP_BLOCKED_HOST_SUFFIXES or DEFAULT_BLOCKED_HOST_SUFFIXES)
    except Exception:
        blocked = set(DEFAULT_BLOCKED_HOST_SUFFIXES)
    suggestions: List[Tuple[str, int, str]] = []

    for domain, cnt in zero_rows:
        host = normalize_host(f"https://{domain}/" if domain and "://" not in domain else domain)
        if not host:
            continue
        if host in contact_hosts:
            continue
        if any(host == s.lower().lstrip(".") or host.endswith("." + s.lower().lstrip(".")) for s in blocked):
            continue
        suggestions.append((host, int(cnt), f"{cnt} zero-page crawls in {days}d, no domain_contacts"))
        if len(suggestions) >= limit:
            break

    return suggestions


def format_denylist_env_lines(suggestions: List[Tuple[str, int, str]]) -> List[str]:
    """Lines suitable for SERP_BLOCKED_HOST_SUFFIXES (comma-separated in .env)."""
    return [host for host, _, _ in suggestions]
