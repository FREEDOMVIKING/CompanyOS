#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DASHBOARD_DIR="$ROOT_DIR/companyos/dashboard"
PID_FILE="$DASHBOARD_DIR/dashboard.pid"
LOG_FILE="$DASHBOARD_DIR/logs/server.log"

mkdir -p "$DASHBOARD_DIR/logs"

python "$ROOT_DIR/companyos/portfolioctl" review \
    >/dev/null 2>&1 || true

if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE")"

    if kill -0 "$PID" 2>/dev/null; then
        echo "Dashboard already running."
        echo "Open: http://127.0.0.1:8765"
        exit 0
    fi

    rm -f "$PID_FILE"
fi

cd "$ROOT_DIR"

nohup python companyos/dashboard/server.py \
    >> "$LOG_FILE" 2>&1 &

PID="$!"
echo "$PID" > "$PID_FILE"

sleep 2

if kill -0 "$PID" 2>/dev/null; then
    echo "Executive dashboard started."
    echo "Open: http://127.0.0.1:8765"
else
    echo "ERROR: Dashboard failed to start."
    echo "Check: $LOG_FILE"
    exit 1
fi
