#!/usr/bin/env python3
"""One-off: set Keyword.is_processed=True when queue has no pending/running work for that keyword.

Run after upgrading workers that now auto-finalize keywords; fixes rows stuck from older builds.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from datetime import datetime, timezone  # noqa: E402

from models.database import SessionLocal, Keyword  # noqa: E402
from models.task_queue import TaskQueue  # noqa: E402


def main() -> int:
    db = SessionLocal()
    updated = 0
    try:
        pending_kw = (
            db.query(Keyword)
            .filter(Keyword.is_processed.is_(False))
            .order_by(Keyword.id)
            .all()
        )
        for kw in pending_kw:
            ever = (
                db.query(TaskQueue)
                .filter(TaskQueue.keyword_id == kw.id)
                .count()
            )
            if ever == 0:
                continue
            open_n = (
                db.query(TaskQueue)
                .filter(
                    TaskQueue.keyword_id == kw.id,
                    TaskQueue.status.in_(("pending", "running")),
                )
                .count()
            )
            if open_n > 0:
                continue
            kw.is_processed = True
            kw.last_crawled_at = datetime.now(timezone.utc)
            updated += 1
        db.commit()
        print(f"Updated {updated} keyword(s) to is_processed=True")
        return 0
    except Exception as e:
        db.rollback()
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
