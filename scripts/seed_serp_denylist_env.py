#!/usr/bin/env python3
"""Write full default SERP denylist to .env as JSON (repair partial overrides)."""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from utils.serp_filters import DEFAULT_BLOCKED_HOST_SUFFIXES  # noqa: E402


def main() -> int:
    env_path = os.path.join(ROOT, ".env")
    hosts = list(DEFAULT_BLOCKED_HOST_SUFFIXES)
    line = "SERP_BLOCKED_HOST_SUFFIXES=" + json.dumps(hosts, ensure_ascii=False)
    with open(env_path, encoding="utf-8") as f:
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
    with open(env_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"Wrote {len(hosts)} hosts to {env_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
