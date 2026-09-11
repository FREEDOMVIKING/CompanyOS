#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PID_FILE="$ROOT_DIR/companyos/dashboard/dashboard.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Dashboard is not running."
    exit 0
fi

PID="$(cat "$PID_FILE")"

if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    echo "Dashboard stopped."
else
    echo "Dashboard process was not active."
fi

rm -f "$PID_FILE"
