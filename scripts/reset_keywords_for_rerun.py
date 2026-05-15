#!/usr/bin/env python3
"""Set all keywords to is_processed=False for a full pipeline rerun."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from models.database import Keyword, SessionLocal  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        n = (
            db.query(Keyword)
            .filter(Keyword.is_processed.is_(True))
            .update({Keyword.is_processed: False}, synchronize_session=False)
        )
        db.commit()
        print(f"Reset is_processed=False for {n} keyword(s)")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
