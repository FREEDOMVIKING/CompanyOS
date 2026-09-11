#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

PID_FILE="${HOME}/companyos/companyos_runtime/phase18201_18300/runtime.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "No Phase 18201-18300 PID file found."
  exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"
if [ -n "${PID:-}" ] && kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "Stopped CompanyOS executive runtime PID $PID"
else
  echo "Runtime was not active."
fi
rm -f "$PID_FILE"
