#!/usr/bin/env python3
"""Test Yandex Cloud Search API (SERP) using .env IAM + folder."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from config.settings import settings  # noqa: E402
from services.serp_service import SerpService  # noqa: E402


def main() -> int:
    print("=" * 60)
    print("YANDEX SEARCH API TEST")
    print("=" * 60)
    if not settings.YANDEX_IAM_TOKEN or not settings.YANDEX_FOLDER_ID:
        print("Set YANDEX_IAM_TOKEN and YANDEX_FOLDER_ID in .env")
        return 1

    if settings.SERP_API_PROVIDER != "yandex":
        print(f"Note: SERP_API_PROVIDER={settings.SERP_API_PROVIDER!r} (set yandex for prod)")

    serp = SerpService()
    serp.provider = "yandex"
    query = "финтех стартап контакты email"
    try:
        results, raw = serp.search(query, country="RU", language="ru", num_results=3)
    except Exception as exc:
        print(f"\nFAILED: {exc}")
        print(
            "\nIf 403: assign role search-api.webSearch.user on folder for your OAuth user."
            "\nDocs: doc/YANDEX_SEARCH_SETUP.md"
        )
        return 1

    print(f"\nOK: {len(results)} result(s) for {query!r}\n")
    for r in results:
        print(f"  [{r.get('position')}] {r.get('url')}")
        print(f"      { (r.get('title') or '')[:80]}")
    print(f"\nraw response keys: {list(raw.keys())}")
    return 0 if results else 2


if __name__ == "__main__":
    raise SystemExit(main())
