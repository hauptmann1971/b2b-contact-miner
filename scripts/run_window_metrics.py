#!/usr/bin/env python3
"""Metrics before/after a pipeline run window (local server time in logs)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from datetime import datetime  # noqa: E402
from sqlalchemy import text  # noqa: E402

from models.database import Contact, CrawlLog, DomainContact, Keyword, SessionLocal  # noqa: E402

T0 = datetime(2026, 5, 15, 11, 26, 0)
T1 = datetime(2026, 5, 15, 11, 28, 10)


def main() -> None:
    db = SessionLocal()
    try:
        email_sql = text(
            "SELECT COUNT(DISTINCT domain_contact_id) FROM contacts "
            "WHERE LOWER(CAST(contact_type AS CHAR)) = 'email'"
        )
        dc_before = db.execute(
            text("SELECT COUNT(*) FROM domain_contacts WHERE created_at < :t0"), {"t0": T0}
        ).scalar()
        c_before = db.execute(
            text("SELECT COUNT(*) FROM contacts WHERE created_at < :t0"), {"t0": T0}
        ).scalar()
        email_before = db.execute(
            text(
                "SELECT COUNT(DISTINCT dc.id) FROM domain_contacts dc "
                "JOIN contacts c ON c.domain_contact_id = dc.id "
                "WHERE LOWER(CAST(c.contact_type AS CHAR)) = 'email' "
                "AND dc.created_at < :t0"
            ),
            {"t0": T0},
        ).scalar()

        run_crawls = (
            db.query(CrawlLog)
            .filter(CrawlLog.crawled_at >= T0, CrawlLog.crawled_at <= T1)
            .count()
        )
        run_zero = (
            db.query(CrawlLog)
            .filter(
                CrawlLog.crawled_at >= T0,
                CrawlLog.crawled_at <= T1,
                CrawlLog.pages_crawled == 0,
            )
            .count()
        )

        dc_after = db.query(DomainContact).count()
        c_after = db.query(Contact).count()
        email_after = db.execute(email_sql).scalar()

        print("BEFORE (created_at < 11:26)")
        print(f"  domain_contacts={dc_before}")
        print(f"  contact_rows={c_before}")
        print(f"  domains_with_email={email_before}")
        if dc_before:
            print(f"  yield_email={100 * email_before / dc_before:.1f}%")

        print("\nIN RUN 11:26-11:28 (crawl_logs)")
        print(f"  new_crawls={run_crawls} zero_page={run_zero}", end="")
        if run_crawls:
            print(f" zero_rate={100 * run_zero / run_crawls:.1f}%")
        else:
            print()

        print("\nAFTER (now)")
        print(f"  domain_contacts={dc_after} (+{dc_after - dc_before})")
        print(f"  contact_rows={c_after} (+{c_after - c_before})")
        print(f"  domains_with_email={email_after} (+{email_after - email_before})")
        if dc_after:
            print(f"  yield_email={100 * email_after / dc_after:.1f}%")

        print("\nKEYWORDS")
        print(
            f"  processed={db.query(Keyword).filter(Keyword.is_processed.is_(True)).count()}/"
            f"{db.query(Keyword).count()}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
