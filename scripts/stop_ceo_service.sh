#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

PIDFILE="$HOME/companyos/.companyos_runtime/ceo_service.pid"

if [ ! -f "$PIDFILE" ]; then
  echo "COMPANYOS_CEO_SERVICE_NOT_RUNNING"
  exit 0
fi

PID="$(cat "$PIDFILE" 2>/dev/null || true)"
if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  sleep 1
fi

rm -f "$PIDFILE"
echo "COMPANYOS_CEO_SERVICE_STOPPED"
