#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "${HOME}/companyos"
RUNTIME_DIR="${HOME}/companyos/companyos_runtime/phase18201_18300"
LOG_DIR="${HOME}/companyos/logs"
PID_FILE="$RUNTIME_DIR/runtime.pid"
LOG_FILE="$LOG_DIR/phase18201_18300.log"

mkdir -p "$RUNTIME_DIR" "$LOG_DIR"

if [ -f "$PID_FILE" ]; then
  OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "${OLD_PID:-}" ] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "CompanyOS executive runtime already running with PID $OLD_PID"
    exit 0
  fi
  rm -f "$PID_FILE"
fi

nohup python -m companyos.executive.runtime >>"$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

sleep 1
if kill -0 "$PID" 2>/dev/null; then
  echo "CompanyOS Phase 18201-18300 started."
  echo "PID: $PID"
  echo "Log: $LOG_FILE"
  echo "Dashboard snapshot: $RUNTIME_DIR/executive_dashboard.json"
else
  echo "Runtime failed to start. Check $LOG_FILE"
  exit 1
fi
