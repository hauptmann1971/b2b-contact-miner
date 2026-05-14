#!/usr/bin/env bash
# Start main.py in the background with a stable absolute log path (no disown).
# Safe to run from any cwd. Override paths with env vars if needed.
set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PATH="${VENV_PATH:-$PROJECT_DIR/venv}"
PYTHON_BIN="${PYTHON_BIN:-$VENV_PATH/bin/python}"
LOG_FILE="${PIPELINE_LOG:-$PROJECT_DIR/logs/pipeline_background.log}"

mkdir -p "$(dirname "$LOG_FILE")"
cd "$PROJECT_DIR"

export PYTHONPATH="${PROJECT_DIR}${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python interpreter not found: $PYTHON_BIN" >&2
  exit 1
fi

nohup "$PYTHON_BIN" main.py >>"$LOG_FILE" 2>&1 </dev/null &
echo "Pipeline started in background (PID $!). Log: $LOG_FILE"
