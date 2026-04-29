#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/b2b-contact-miner}"
VENV_PATH="${VENV_PATH:-$PROJECT_DIR/venv}"
PYTHON_BIN="${PYTHON_BIN:-$VENV_PATH/bin/python}"
LOG_DIR="${LOG_DIR:-$PROJECT_DIR/logs}"
LOCK_FILE="${LOCK_FILE:-/tmp/b2b-contact-miner-nightly.lock}"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python interpreter not found: $PYTHON_BIN" >&2
  exit 1
fi

export PYTHONUNBUFFERED=1

timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
echo "[$timestamp] Starting nightly pipeline run..."

# Prevent overlapping nightly runs.
flock -n "$LOCK_FILE" \
  "$PYTHON_BIN" main.py >> "$LOG_DIR/pipeline_nightly.log" 2>&1

exit_code=$?
timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
echo "[$timestamp] Nightly pipeline finished with exit code: $exit_code"
exit "$exit_code"
