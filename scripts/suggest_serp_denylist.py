#!/usr/bin/env python3
"""Suggest SERP_BLOCKED_HOST_SUFFIXES from zero-page crawl history."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from models.database import SessionLocal  # noqa: E402
from utils.serp_denylist import format_denylist_env_lines, suggest_blocked_hosts  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        suggestions = suggest_blocked_hosts(db)
        if not suggestions:
            print("No new denylist suggestions (threshold not met or all blocked already).")
            return
        print("Suggested hosts to add to SERP_BLOCKED_HOST_SUFFIXES:")
        for host, cnt, reason in suggestions:
            print(f"  {host}  # {reason}")
        print("\nComma-separated (append to .env):")
        print(",".join(format_denylist_env_lines(suggestions)))
    finally:
        db.close()


if __name__ == "__main__":
    main()
