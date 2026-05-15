#!/usr/bin/env python3
"""Print pipeline quality metrics for SERP / crawl / extract stages."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from datetime import datetime, timedelta, timezone  # noqa: E402

from sqlalchemy import func, text  # noqa: E402

from config.settings import settings  # noqa: E402
from models.database import (  # noqa: E402
    Contact,
    CrawlLog,
    DomainContact,
    Keyword,
    SessionLocal,
)
from models.task_queue import TaskQueue  # noqa: E402
from utils.serp_denylist import suggest_blocked_hosts  # noqa: E402


def main() -> None:
    db = SessionLocal()
    since = datetime.now(timezone.utc) - timedelta(days=7)
    try:
        print("=== Settings (effective defaults + .env) ===")
        print(f"  SERP provider: {settings.SERP_API_PROVIDER}")
        print(f"  results/keyword: {settings.SEARCH_RESULTS_PER_KEYWORD}")
        print(f"  max pages/domain: {settings.MAX_PAGES_PER_DOMAIN}")
        print(f"  domain timeout: {settings.DOMAIN_CRAWL_TIMEOUT}s")
        print(f"  LLM extraction: {settings.USE_LLM_EXTRACTION}")

        print("\n=== Keywords ===")
        total_kw = db.query(Keyword).count()
        done_kw = db.query(Keyword).filter(Keyword.is_processed.is_(True)).count()
        print(f"  total={total_kw} processed={done_kw} pending={total_kw - done_kw}")

        print("\n=== Task queue (all time) ===")
        for st in ("pending", "running", "completed", "failed"):
            n = db.query(TaskQueue).filter(TaskQueue.status == st).count()
            print(f"  {st}: {n}")
        for tt in ("search_keyword", "crawl_domain", "extract_contacts"):
            failed = (
                db.query(TaskQueue)
                .filter(TaskQueue.task_type == tt, TaskQueue.status == "failed")
                .count()
            )
            print(f"  failed {tt}: {failed}")

        print("\n=== Crawl logs (7d) ===")
        logs = db.query(CrawlLog).filter(CrawlLog.crawled_at >= since)
        total_c = logs.count()
        zero_c = logs.filter(CrawlLog.pages_crawled == 0).count()
        timeout_c = logs.filter(
            CrawlLog.error_message.isnot(None),
            CrawlLog.error_message.ilike("%timeout%"),
        ).count()
        print(f"  crawls={total_c} zero_pages={zero_c} timeouts={timeout_c}")
        if total_c:
            print(f"  zero_page_rate={100.0 * zero_c / total_c:.1f}%")
            print(f"  timeout_rate={100.0 * timeout_c / total_c:.1f}%")

        print("\n=== Contacts ===")
        n_dc = db.query(DomainContact).count()
        n_c = db.query(Contact).count()
        with_email = db.execute(
            text(
                "SELECT COUNT(DISTINCT domain_contact_id) FROM contacts "
                "WHERE LOWER(CAST(contact_type AS CHAR)) = 'email'"
            )
        ).scalar()
        llm_dc = (
            db.query(DomainContact)
            .filter(DomainContact.extraction_method == "llm")
            .count()
        )
        print(f"  domain_contacts={n_dc} contact_rows={n_c}")
        print(f"  domains_with_email={with_email}")
        if n_dc:
            print(f"  yield domains with email={100.0 * with_email / n_dc:.1f}%")
        print(f"  extraction_method=llm count={llm_dc}")

        nonempty_json = 0
        for row in db.query(DomainContact.contacts_json).limit(200).all():
            p = row[0] or {}
            if isinstance(p, dict) and (p.get("emails") or p.get("telegram")):
                nonempty_json += 1
        print(f"  contacts_json with data (sample 200)={nonempty_json}")

        print("\n=== Top zero-page reasons (7d) ===")
        reasons = (
            db.query(CrawlLog.error_message, func.count(CrawlLog.id))
            .filter(CrawlLog.crawled_at >= since, CrawlLog.pages_crawled == 0)
            .group_by(CrawlLog.error_message)
            .order_by(func.count(CrawlLog.id).desc())
            .limit(8)
            .all()
        )
        for reason, cnt in reasons:
            print(f"  {cnt}x {(reason or 'null')[:70]}")

        print("\n=== Suggested SERP denylist (zero-page, no contacts) ===")
        suggestions = suggest_blocked_hosts(db)
        if not suggestions:
            print("  (none — run scripts/suggest_serp_denylist.py for details)")
        else:
            for host, cnt, reason in suggestions[:12]:
                print(f"  {host} ({cnt}x) — {reason}")
            print("  Run: python scripts/suggest_serp_denylist.py")
    finally:
        db.close()


if __name__ == "__main__":
    main()
