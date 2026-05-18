#!/usr/bin/env python3
"""Merge suggested SERP denylist hosts into .env (idempotent)."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from models.database import SessionLocal  # noqa: E402
from utils.serp_denylist import suggest_blocked_hosts  # noqa: E402
from utils.serp_constants import DEFAULT_BLOCKED_HOST_SUFFIXES  # noqa: E402


def _parse_env_hosts(env_text: str) -> list[str]:
    match = re.search(r"^SERP_BLOCKED_HOST_SUFFIXES=(.*)$", env_text, re.MULTILINE)
    if not match:
        return []
    raw = match.group(1).strip().strip('"').strip("'")
    if not raw:
        return []
    if raw.startswith("["):
        import json

        try:
            return list(json.loads(raw))
        except json.JSONDecodeError:
            pass
    return [h.strip() for h in raw.split(",") if h.strip()]


def _write_env_hosts(path: str, hosts: list[str]) -> None:
    line = "SERP_BLOCKED_HOST_SUFFIXES=" + json.dumps(hosts, ensure_ascii=False)
    with open(path, encoding="utf-8") as f:
        content = f.read()
    if re.search(r"^SERP_BLOCKED_HOST_SUFFIXES=", content, re.MULTILINE):
        content = re.sub(
            r"^SERP_BLOCKED_HOST_SUFFIXES=.*$",
            line,
            content,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        if content and not content.endswith("\n"):
            content += "\n"
        content += line + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


EXIT_OK = 0
EXIT_NO_SUGGESTIONS = 1
EXIT_ALREADY_PRESENT = 2


def apply_suggestions(env_file: str, dry_run: bool, suggestions: list) -> int:
    if not suggestions:
        print("No new hosts to add.")
        return EXIT_NO_SUGGESTIONS

    current = list(DEFAULT_BLOCKED_HOST_SUFFIXES)
    if os.path.isfile(env_file):
        env_hosts = _parse_env_hosts(open(env_file, encoding="utf-8").read())
        for h in env_hosts:
            if h not in current:
                current.append(h)

    added: list[str] = []
    for host, _cnt, reason in suggestions:
        h = host.lower().strip()
        if h not in {c.lower() for c in current}:
            current.append(h)
            added.append(h)
            print(f"  + {h}  # {reason}")

    if not added:
        print("Suggestions already present in denylist.")
        return EXIT_ALREADY_PRESENT

    print(f"\nAdding {len(added)} host(s). Total denylist size: {len(current)}")
    if dry_run:
        print("(dry-run, .env not modified)")
        return EXIT_OK

    _write_env_hosts(env_file, current)
    print(f"Updated {env_file}")
    return EXIT_OK


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply SERP denylist suggestions to .env")
    parser.add_argument(
        "--env-file",
        default=os.path.join(ROOT, ".env"),
        help="Path to .env (default: project root)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print only, do not write")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        suggestions = suggest_blocked_hosts(db)
    finally:
        db.close()

    return apply_suggestions(args.env_file, args.dry_run, suggestions)


if __name__ == "__main__":
    raise SystemExit(main())
