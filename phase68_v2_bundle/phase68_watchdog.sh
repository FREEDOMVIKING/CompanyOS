#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="${HOME}/companyos"
INTERVAL="${COMPANYOS_HEALTH_INTERVAL_SECONDS:-300}"

cd "$ROOT" || exit 1
export PYTHONPATH="$ROOT:$ROOT/companyos"

echo "COMPANYOS_PHASE68_WATCHDOG: STARTED"
echo "INTERVAL_SECONDS: $INTERVAL"

while true; do
  python phase68_health.py || true
  python phase68_heartbeat.py || true
  python phase67_v2_reconcile_once.py || true
  sleep "$INTERVAL"
done
