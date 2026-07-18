#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PID_FILE="$ROOT_DIR/companyos/storefront/storefront.pid"

if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE")"

    if kill -0 "$PID" 2>/dev/null; then
        echo "Storefront status: RUNNING"
        echo "Address: http://127.0.0.1:8780"
        exit 0
    fi
fi

echo "Storefront status: STOPPED"
exit 1
