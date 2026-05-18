#!/usr/bin/env python3
"""Metrics before/after a pipeline run window."""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from datetime import datetime  # noqa: E402
from sqlalchemy import text  # noqa: E402

from models.database import CrawlLog, Keyword, SessionLocal  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True, help="YYYY-MM-DD HH:MM:SS")
    p.add_argument("--end", required=True, help="YYYY-MM-DD HH:MM:SS")
    args = p.parse_args()
    t0 = datetime.strptime(args.start, "%Y-%m-%d %H:%M:%S")
    t1 = datetime.strptime(args.end, "%Y-%m-%d %H:%M:%S")

    db = SessionLocal()
    try:
        email_sql = text(
            "SELECT COUNT(DISTINCT domain_contact_id) FROM contacts "
            "WHERE LOWER(CAST(contact_type AS CHAR)) = 'email'"
        )
        dc_b = db.execute(
            text("SELECT COUNT(*) FROM domain_contacts WHERE created_at < :t0"), {"t0": t0}
        ).scalar()
        c_b = db.execute(
            text("SELECT COUNT(*) FROM contacts WHERE created_at < :t0"), {"t0": t0}
        ).scalar()
        e_b = db.execute(
            text(
                "SELECT COUNT(DISTINCT dc.id) FROM domain_contacts dc "
                "JOIN contacts c ON c.domain_contact_id = dc.id "
                "WHERE LOWER(CAST(c.contact_type AS CHAR)) = 'email' "
                "AND dc.created_at < :t0"
            ),
            {"t0": t0},
        ).scalar()
        cr = db.query(CrawlLog).filter(CrawlLog.crawled_at >= t0, CrawlLog.crawled_at <= t1).count()
        zr = db.query(CrawlLog).filter(
            CrawlLog.crawled_at >= t0, CrawlLog.crawled_at <= t1, CrawlLog.pages_crawled == 0
        ).count()
        dc_a = db.execute(text("SELECT COUNT(*) FROM domain_contacts")).scalar()
        c_a = db.execute(text("SELECT COUNT(*) FROM contacts")).scalar()
        e_a = db.execute(email_sql).scalar()

        print(f"Window: {args.start} .. {args.end}")
        print(f"\nBEFORE (< start)")
        print(f"  domain_contacts={dc_b}  contact_rows={c_b}  domains_with_email={e_b}")
        if dc_b:
            print(f"  yield_email={100 * e_b / dc_b:.1f}%")
        print(f"\nIN RUN (crawl_logs)")
        print(f"  crawls={cr}  zero_page={zr}", end="")
        print(f"  zero_rate={100 * zr / cr:.1f}%" if cr else "")
        print(f"\nAFTER (totals)")
        print(f"  domain_contacts={dc_a} (+{dc_a - dc_b})")
        print(f"  contact_rows={c_a} (+{c_a - c_b})")
        print(f"  domains_with_email={e_a} (+{e_a - e_b})")
        if dc_a:
            print(f"  yield_email={100 * e_a / dc_a:.1f}%")
        kw = db.query(Keyword).count()
        done = db.query(Keyword).filter(Keyword.is_processed.is_(True)).count()
        print(f"\nkeywords processed={done}/{kw}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
