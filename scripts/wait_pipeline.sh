#!/usr/bin/env bash
# Wait for main.py to exit (max 60 min).
set -euo pipefail
LOG="${PIPELINE_LOG:-/opt/b2b-contact-miner/logs/pipeline_background.log}"
for i in $(seq 1 120); do
  if ! pgrep -f '/opt/b2b-contact-miner/venv/bin/python main.py' >/dev/null 2>&1; then
    echo "Pipeline stopped after $((i * 30))s"
    tail -8 "$LOG"
    exit 0
  fi
  grep -E 'Queue Status|Pipeline completed' "$LOG" 2>/dev/null | tail -1 || true
  sleep 30
done
echo "Timeout waiting for pipeline"
exit 1
