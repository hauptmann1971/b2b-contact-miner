"""
Batch smoke test (10-20 domains) with quality report.
Usage:
  py -m checkers.smoke_pipeline_quality --limit 15
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal, SearchResult, CrawlLog, DomainContact
from services.crawler_service import CrawlerService
from services.extraction_service import ExtractionService


def _snapshot_stats(hours: int = 24) -> dict:
    db = SessionLocal()
    try:
        since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
        total_crawls = db.query(CrawlLog).filter(CrawlLog.crawled_at >= since).count()
        zero_page = db.query(CrawlLog).filter(
            CrawlLog.crawled_at >= since,
            CrawlLog.pages_crawled == 0
        ).count()
        contacts_total = db.query(DomainContact).filter(DomainContact.created_at >= since).count()

        social_with_data = 0
        for row in db.query(DomainContact.contacts_json).filter(DomainContact.created_at >= since).all():
            payload = row[0] or {}
            social = payload.get("social") if isinstance(payload, dict) else None
            if isinstance(social, dict) and any(bool(v) for v in social.values()):
                social_with_data += 1

        success_rate = ((total_crawls - zero_page) / total_crawls * 100) if total_crawls else 100.0
        social_coverage = (social_with_data / contacts_total * 100) if contacts_total else 0.0
        return {
            "window_hours": hours,
            "total_crawls": total_crawls,
            "zero_page_crawls": zero_page,
            "crawl_success_rate": round(success_rate, 2),
            "domain_contacts": contacts_total,
            "domains_with_social": social_with_data,
            "social_coverage_rate": round(social_coverage, 2),
        }
    finally:
        db.close()


async def run_smoke(limit: int):
    db = SessionLocal()
    crawler = CrawlerService()
    extractor = ExtractionService()
    try:
        urls = [
            row[0]
            for row in db.query(SearchResult.url)
            .filter(SearchResult.url.isnot(None))
            .order_by(SearchResult.created_at.desc())
            .limit(limit)
            .all()
        ]
    finally:
        db.close()

    if not urls:
        print("No search_results URLs found. Run pipeline search stage first.")
        return

    before = _snapshot_stats(hours=24)
    print("=== SMOKE BEFORE ===")
    print(json.dumps(before, ensure_ascii=False, indent=2))

    processed = 0
    with_contacts = 0
    failures = 0
    zero_page = 0

    for url in urls:
        processed += 1
        try:
            crawl_data = await crawler.crawl_domain(url)
            if crawl_data.get("pages_crawled", 0) == 0:
                zero_page += 1
            contacts, _ = extractor.extract_contacts(crawl_data.get("content", []))
            if contacts.emails or contacts.telegram_links or contacts.linkedin_links or any(
                bool(v) for v in (contacts.social_links or {}).values()
            ):
                with_contacts += 1
            logger.info(f"[{processed}/{len(urls)}] {urlparse(url).netloc} done")
        except Exception as e:
            failures += 1
            logger.warning(f"[{processed}/{len(urls)}] Failed for {url}: {e}")

    after = _snapshot_stats(hours=24)
    print("\n=== SMOKE AFTER ===")
    print(json.dumps(after, ensure_ascii=False, indent=2))
    print("\n=== RUN SUMMARY ===")
    print(json.dumps({
        "sample_size": len(urls),
        "processed": processed,
        "with_contacts": with_contacts,
        "with_contacts_rate": round((with_contacts / processed * 100), 2) if processed else 0.0,
        "zero_page_in_run": zero_page,
        "zero_page_rate_in_run": round((zero_page / processed * 100), 2) if processed else 0.0,
        "failures": failures,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run 10-20 domain smoke quality test")
    parser.add_argument("--limit", type=int, default=15, help="Number of domains to test (10-20 recommended)")
    args = parser.parse_args()
    capped = max(1, min(args.limit, 20))
    asyncio.run(run_smoke(capped))
