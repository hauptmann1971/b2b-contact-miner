#!/usr/bin/env python3
"""Print keywords with is_processed=0 and their task_queue breakdown."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from sqlalchemy import func  # noqa: E402

from models.database import Keyword, SessionLocal  # noqa: E402
from models.task_queue import TaskQueue  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        pending = (
            db.query(Keyword)
            .filter(Keyword.is_processed.is_(False))
            .order_by(Keyword.id)
            .all()
        )
        print(f"keywords is_processed=0: {len(pending)}")
        for k in pending:
            by_status = dict(
                db.query(TaskQueue.status, func.count(TaskQueue.id))
                .filter(TaskQueue.keyword_id == k.id)
                .group_by(TaskQueue.status)
                .all()
            )
            open_n = (
                db.query(TaskQueue)
                .filter(
                    TaskQueue.keyword_id == k.id,
                    TaskQueue.status.in_(("pending", "running")),
                )
                .count()
            )
            total = (
                db.query(TaskQueue).filter(TaskQueue.keyword_id == k.id).count()
            )
            print(
                f"  id={k.id} | {k.keyword!r} | {k.language}/{k.country} | "
                f"open={open_n} total={total} | status={by_status}"
            )
            if open_n:
                rows = (
                    db.query(
                        TaskQueue.id,
                        TaskQueue.task_type,
                        TaskQueue.status,
                        TaskQueue.locked_by,
                        TaskQueue.locked_at,
                        TaskQueue.depends_on_task_id,
                    )
                    .filter(
                        TaskQueue.keyword_id == k.id,
                        TaskQueue.status.in_(("pending", "running")),
                    )
                    .limit(20)
                    .all()
                )
                for r in rows:
                    parent_status = None
                    if r.depends_on_task_id:
                        parent = (
                            db.query(TaskQueue.status)
                            .filter(TaskQueue.id == r.depends_on_task_id)
                            .first()
                        )
                        parent_status = parent[0] if parent else "missing"
                    print(
                        f"    task {r.id} {r.task_type} {r.status} "
                        f"dep={r.depends_on_task_id} parent_status={parent_status} "
                        f"locked_by={r.locked_by}"
                    )
        # Sample blocked-by-failed-parent
        for tid in (287, 298, 372, 373):
            t = db.query(TaskQueue).filter(TaskQueue.id == tid).first()
            if t:
                err = (t.error_message or "")[:80]
                print(
                    f"parent task {tid}: type={t.task_type} status={t.status} "
                    f"keyword_id={t.keyword_id} err={err!r}"
                )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
