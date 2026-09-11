#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
STORE_DIR="$ROOT_DIR/companyos/storefront"
PID_FILE="$STORE_DIR/storefront.pid"
LOG_FILE="$STORE_DIR/logs/server.log"

mkdir -p "$STORE_DIR/logs"

python -m agents.storefront_agent >/dev/null

if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE")"

    if kill -0 "$PID" 2>/dev/null; then
        echo "Storefront already running."
        echo "Open: http://127.0.0.1:8780"
        exit 0
    fi

    rm -f "$PID_FILE"
fi

cd "$ROOT_DIR"

nohup python companyos/storefront/server.py \
    >> "$LOG_FILE" 2>&1 &

PID="$!"
echo "$PID" > "$PID_FILE"

sleep 2

if kill -0 "$PID" 2>/dev/null; then
    echo "Storefront started."
    echo "Open: http://127.0.0.1:8780"
else
    echo "ERROR: Storefront failed to start."
    echo "Check: $LOG_FILE"
    exit 1
fi
