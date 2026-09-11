#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PID_FILE="$ROOT_DIR/companyos/dashboard/dashboard.pid"

if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE")"

    if kill -0 "$PID" 2>/dev/null; then
        echo "Dashboard status: RUNNING"
        echo "Address: http://127.0.0.1:8765"
        exit 0
    fi
fi

echo "Dashboard status: STOPPED"
exit 1
