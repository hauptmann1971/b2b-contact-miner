"""
Run weekly smoke benchmark and compare against previous report.

Usage:
  py checkers/run_weekly_smoke.py --limit 15
  py checkers/run_weekly_smoke.py --limit 15 --write-db
  py checkers/run_weekly_smoke.py --limit 15 --min-with-contacts-rate 25 --max-zero-page-rate 45 --max-failures 0
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


def _evaluate_kpi_gate(summary: dict, min_with_contacts_rate: float, max_zero_page_rate: float, max_failures: int) -> int:
    with_contacts_rate = float(summary.get("with_contacts_rate", 0.0))
    zero_page_rate = float(summary.get("zero_page_rate_in_run", 100.0))
    failures = int(summary.get("failures", 0))

    reasons = []
    if with_contacts_rate < min_with_contacts_rate:
        reasons.append(
            f"with_contacts_rate={with_contacts_rate} < min_with_contacts_rate={min_with_contacts_rate}"
        )
    if zero_page_rate > max_zero_page_rate:
        reasons.append(
            f"zero_page_rate_in_run={zero_page_rate} > max_zero_page_rate={max_zero_page_rate}"
        )
    if failures > max_failures:
        reasons.append(
            f"failures={failures} > max_failures={max_failures}"
        )

    print("\n=== KPI GATE ===")
    if reasons:
        print("FAIL")
        for reason in reasons:
            print(f"- {reason}")
        return 2

    print("PASS")
    print(
        f"- with_contacts_rate={with_contacts_rate} (min {min_with_contacts_rate}), "
        f"zero_page_rate_in_run={zero_page_rate} (max {max_zero_page_rate}), "
        f"failures={failures} (max {max_failures})"
    )
    return 0


async def main():
    parser = argparse.ArgumentParser(description="Run weekly smoke and compare with previous report")
    parser.add_argument("--limit", type=int, default=15, help="Number of domains to test")
    parser.add_argument("--write-db", action="store_true", help="Persist smoke results to DB")
    parser.add_argument("--min-with-contacts-rate", type=float, default=20.0, help="Fail if with_contacts_rate is below this value")
    parser.add_argument("--max-zero-page-rate", type=float, default=60.0, help="Fail if zero_page_rate_in_run is above this value")
    parser.add_argument("--max-failures", type=int, default=0, help="Fail if failures is above this value")
    args = parser.parse_args()

    capped = max(1, min(args.limit, 20))
    await run_smoke(capped, args.write_db, report_file=None)

    reports_dir = Path("artifacts") / "smoke-reports"
    exit_code = 0
    try:
        newest, previous = _latest_two_reports(reports_dir)
        _print_quick_delta(newest, previous)
        newest_report = _load_report(newest)
        summary = newest_report.get("summary", {})
        exit_code = _evaluate_kpi_gate(
            summary,
            min_with_contacts_rate=args.min_with_contacts_rate,
            max_zero_page_rate=args.max_zero_page_rate,
            max_failures=args.max_failures,
        )
    except FileNotFoundError:
        print("\nNot enough reports for comparison yet (need at least 2).")
        # Still evaluate gate against latest single report if available.
        reports = sorted(reports_dir.glob("smoke_quality_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if reports:
            newest_report = _load_report(reports[0])
            summary = newest_report.get("summary", {})
            exit_code = _evaluate_kpi_gate(
                summary,
                min_with_contacts_rate=args.min_with_contacts_rate,
                max_zero_page_rate=args.max_zero_page_rate,
                max_failures=args.max_failures,
            )

    raise SystemExit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
