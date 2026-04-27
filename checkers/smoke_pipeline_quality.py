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
from pathlib import Path
from urllib.parse import urlparse

from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from models.database import SessionLocal, SearchResult, CrawlLog, DomainContact, Contact, ContactType
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


def _save_smoke_result_to_db(url: str, crawl_data: dict, contacts) -> None:
    """Persist smoke run result into crawl_logs/domain_contacts/contacts."""
    db = SessionLocal()
    try:
        search_result = db.query(SearchResult).filter(SearchResult.url == url).order_by(SearchResult.id.desc()).first()
        if not search_result:
            # Smoke can run on urls that are not tied to existing search rows.
            return

        crawl_log = CrawlLog(
            domain=crawl_data.get("domain") or urlparse(url).netloc,
            url=url,
            status_code=200,
            pages_crawled=crawl_data.get("pages_crawled", 0),
            duration_seconds=int(crawl_data.get("duration", 0)),
            error_message=(crawl_data.get("zero_page_reason") if crawl_data.get("pages_crawled", 0) == 0 else None),
        )
        db.add(crawl_log)

        contacts_data = {
            "emails": contacts.emails,
            "telegram": contacts.telegram_links,
            "linkedin": contacts.linkedin_links,
            "phones": contacts.phone_numbers if hasattr(contacts, "phone_numbers") else [],
            "social": contacts.social_links if hasattr(contacts, "social_links") else {},
        }

        domain_contact = DomainContact(
            search_result_id=search_result.id,
            domain=urlparse(url).netloc,
            tags=["smoke-benchmark"],
            contacts_json=contacts_data,
            confidence_score=0,
            extraction_method="llm" if settings.USE_LLM_EXTRACTION else "regex",
        )
        db.add(domain_contact)
        db.flush()

        def add_contact(contact_type: ContactType, value: str):
            db.add(Contact(domain_contact_id=domain_contact.id, contact_type=contact_type, value=value))

        for email in contacts.emails:
            add_contact(ContactType.EMAIL, email)
        for tg in contacts.telegram_links:
            add_contact(ContactType.TELEGRAM, tg)
        for li in contacts.linkedin_links:
            add_contact(ContactType.LINKEDIN, li)
        social_map = {
            "x": ContactType.X,
            "facebook": ContactType.FACEBOOK,
            "instagram": ContactType.INSTAGRAM,
            "youtube": ContactType.YOUTUBE,
        }
        for platform, links in (contacts.social_links or {}).items():
            mapped = social_map.get(platform)
            if not mapped:
                continue
            for link in links:
                add_contact(mapped, link)

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _build_report_payload(before: dict, after: dict, summary: dict) -> dict:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "before": before,
        "after": after,
        "summary": summary,
    }


def _save_report(report_payload: dict, report_file: str = None) -> str:
    reports_dir = Path("artifacts") / "smoke-reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    if report_file:
        target = Path(report_file)
        if not target.is_absolute():
            target = Path.cwd() / target
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = reports_dir / f"smoke_quality_{timestamp}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(target)


async def run_smoke(limit: int, write_db: bool, report_file: str = None):
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
            if write_db:
                _save_smoke_result_to_db(url, crawl_data, contacts)
            logger.info(f"[{processed}/{len(urls)}] {urlparse(url).netloc} done")
        except Exception as e:
            failures += 1
            logger.warning(f"[{processed}/{len(urls)}] Failed for {url}: {e}")

    after = _snapshot_stats(hours=24)
    print("\n=== SMOKE AFTER ===")
    print(json.dumps(after, ensure_ascii=False, indent=2))
    print("\n=== RUN SUMMARY ===")
    summary = {
        "sample_size": len(urls),
        "processed": processed,
        "write_db": write_db,
        "with_contacts": with_contacts,
        "with_contacts_rate": round((with_contacts / processed * 100), 2) if processed else 0.0,
        "zero_page_in_run": zero_page,
        "zero_page_rate_in_run": round((zero_page / processed * 100), 2) if processed else 0.0,
        "failures": failures,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    report_payload = _build_report_payload(before, after, summary)
    report_path = _save_report(report_payload, report_file=report_file)
    print(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run 10-20 domain smoke quality test")
    parser.add_argument("--limit", type=int, default=15, help="Number of domains to test (10-20 recommended)")
    parser.add_argument("--write-db", action="store_true", help="Persist smoke results to crawl_logs/domain_contacts/contacts")
    parser.add_argument("--report-file", type=str, default="", help="Optional path for JSON report output")
    args = parser.parse_args()
    capped = max(1, min(args.limit, 20))
    asyncio.run(run_smoke(capped, args.write_db, args.report_file.strip() or None))
