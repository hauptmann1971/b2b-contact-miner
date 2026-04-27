"""
Compare two smoke quality JSON reports and print KPI deltas.

Usage:
  py checkers/compare_smoke_reports.py
  py checkers/compare_smoke_reports.py --new artifacts/smoke-reports/new.json --old artifacts/smoke-reports/old.json
"""
import argparse
import json
from pathlib import Path
from typing import Dict, Tuple


def _load_report(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_two_reports(reports_dir: Path) -> Tuple[Path, Path]:
    reports = sorted(reports_dir.glob("smoke_quality_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if len(reports) < 2:
        raise FileNotFoundError("Need at least 2 smoke reports to compare.")
    return reports[0], reports[1]


def _delta(new_val: float, old_val: float) -> float:
    return round(float(new_val) - float(old_val), 2)


def main():
    parser = argparse.ArgumentParser(description="Compare smoke quality reports and show KPI deltas")
    parser.add_argument("--new", type=str, default="", help="Path to newer smoke report JSON")
    parser.add_argument("--old", type=str, default="", help="Path to older smoke report JSON")
    args = parser.parse_args()

    if args.new and args.old:
        new_path = Path(args.new)
        old_path = Path(args.old)
    else:
        new_path, old_path = _latest_two_reports(Path("artifacts") / "smoke-reports")

    if not new_path.exists() or not old_path.exists():
        raise FileNotFoundError(f"Report not found. new={new_path}, old={old_path}")

    new_report = _load_report(new_path)
    old_report = _load_report(old_path)

    new_sum = new_report.get("summary", {})
    old_sum = old_report.get("summary", {})

    metrics = {
        "with_contacts_rate": (
            new_sum.get("with_contacts_rate", 0.0),
            old_sum.get("with_contacts_rate", 0.0),
            "higher_is_better",
        ),
        "zero_page_rate_in_run": (
            new_sum.get("zero_page_rate_in_run", 0.0),
            old_sum.get("zero_page_rate_in_run", 0.0),
            "lower_is_better",
        ),
        "failures": (
            new_sum.get("failures", 0.0),
            old_sum.get("failures", 0.0),
            "lower_is_better",
        ),
    }

    print("=== SMOKE REPORT COMPARISON ===")
    print(f"new: {new_path}")
    print(f"old: {old_path}")
    for name, (new_val, old_val, direction) in metrics.items():
        d = _delta(new_val, old_val)
        trend = "improved"
        if direction == "higher_is_better" and d < 0:
            trend = "regressed"
        if direction == "lower_is_better" and d > 0:
            trend = "regressed"
        print(f"- {name}: new={new_val}, old={old_val}, delta={d:+}, {trend}")


if __name__ == "__main__":
    main()
