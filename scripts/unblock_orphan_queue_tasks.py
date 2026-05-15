#!/usr/bin/env python3
"""Clear depends_on_task_id on pending tasks blocked by a failed parent (legacy queue repair)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from models.database import SessionLocal  # noqa: E402
from models.task_queue import TaskQueue  # noqa: E402
from workers.db_task_queue import DatabaseTaskQueue  # noqa: E402


def main() -> int:
    db = SessionLocal()
    cleared = 0
    try:
        pending = (
            db.query(TaskQueue)
            .filter(TaskQueue.status == "pending", TaskQueue.depends_on_task_id.isnot(None))
            .all()
        )
        for task in pending:
            parent = (
                db.query(TaskQueue)
                .filter(TaskQueue.id == task.depends_on_task_id)
                .first()
            )
            if DatabaseTaskQueue._dependency_satisfied(parent, task):
                continue
            if parent and parent.status == "failed":
                task.depends_on_task_id = None
                cleared += 1
        db.commit()
        print(f"Cleared depends_on_task_id on {cleared} pending task(s)")
        return 0
    except Exception as e:
        db.rollback()
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
