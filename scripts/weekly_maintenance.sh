#!/usr/bin/env bash
# Weekly: quality report, apply SERP denylist, queue hygiene. Install in cron:
#   0 3 * * 0 root /opt/b2b-contact-miner/scripts/weekly_maintenance.sh >> /opt/b2b-contact-miner/logs/weekly_maintenance.log 2>&1
set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
PYTHON="${PYTHON:-$PROJECT_DIR/venv/bin/python}"
LOG_DIR="${LOG_DIR:-$PROJECT_DIR/logs}"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"
export PYTHONPATH="${PROJECT_DIR}${PYTHONPATH:+:$PYTHONPATH}"

echo "=== weekly_maintenance $(date -Iseconds) ==="

"$PYTHON" scripts/pipeline_quality_report.py

"$PYTHON" scripts/apply_serp_denylist.py --env-file "$PROJECT_DIR/.env" || true

"$PYTHON" scripts/unblock_orphan_queue_tasks.py || true

"$PYTHON" scripts/fix_mysql_autoincrement_ids.py || true

echo "=== done ==="
