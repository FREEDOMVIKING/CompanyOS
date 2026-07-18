#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PID_FILE="$ROOT_DIR/companyos/storefront/storefront.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Storefront is not running."
    exit 0
fi

PID="$(cat "$PID_FILE")"

if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    echo "Storefront stopped."
else
    echo "Storefront process was not active."
fi

rm -f "$PID_FILE"
