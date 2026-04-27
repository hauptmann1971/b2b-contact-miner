"""
Run weekly smoke benchmark and compare against previous report.

Usage:
  py checkers/run_weekly_smoke.py --limit 15
  py checkers/run_weekly_smoke.py --limit 15 --write-db
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from checkers.smoke_pipeline_quality import run_smoke
from checkers.compare_smoke_reports import _latest_two_reports, _load_report, _delta


def _print_quick_delta(new_report_path: Path, old_report_path: Path) -> None:
    new_report = _load_report(new_report_path)
    old_report = _load_report(old_report_path)
    new_sum = new_report.get("summary", {})
    old_sum = old_report.get("summary", {})

    wc_new = float(new_sum.get("with_contacts_rate", 0.0))
    wc_old = float(old_sum.get("with_contacts_rate", 0.0))
    zp_new = float(new_sum.get("zero_page_rate_in_run", 0.0))
    zp_old = float(old_sum.get("zero_page_rate_in_run", 0.0))

    print("\n=== WEEKLY DELTA ===")
    print(f"with_contacts_rate: {wc_old} -> {wc_new} (delta={_delta(wc_new, wc_old):+})")
    print(f"zero_page_rate_in_run: {zp_old} -> {zp_new} (delta={_delta(zp_new, zp_old):+})")


async def main():
    parser = argparse.ArgumentParser(description="Run weekly smoke and compare with previous report")
    parser.add_argument("--limit", type=int, default=15, help="Number of domains to test")
    parser.add_argument("--write-db", action="store_true", help="Persist smoke results to DB")
    args = parser.parse_args()

    capped = max(1, min(args.limit, 20))
    await run_smoke(capped, args.write_db, report_file=None)

    reports_dir = Path("artifacts") / "smoke-reports"
    try:
        newest, previous = _latest_two_reports(reports_dir)
        _print_quick_delta(newest, previous)
    except FileNotFoundError:
        print("\nNot enough reports for comparison yet (need at least 2).")


if __name__ == "__main__":
    asyncio.run(main())
