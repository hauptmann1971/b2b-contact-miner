#!/usr/bin/env python3
"""Re-queue failed search_keyword tasks (after AUTO_INCREMENT / SERP fixes)."""
import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from models.database import SessionLocal  # noqa: E402
from models.task_queue import TaskQueue  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        failed = (
            db.query(TaskQueue)
            .filter(
                TaskQueue.task_type == "search_keyword",
                TaskQueue.status == "failed",
            )
            .all()
        )
        if not failed:
            print("No failed search_keyword tasks.")
            return 0

        for task in failed:
            task.status = "pending"
            task.retry_count = 0
            task.error_message = None
            task.locked_at = None
            task.locked_by = None
            task.completed_at = None
            task.started_at = None

        db.commit()
        print(f"Reset {len(failed)} failed search_keyword task(s) to pending")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
