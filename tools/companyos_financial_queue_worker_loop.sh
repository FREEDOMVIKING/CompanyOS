#!/data/data/com.termux/files/usr/bin/bash
set -u

cd "$HOME/companyos" || exit 1

INTERVAL="${COMPANYOS_FINANCIAL_QUEUE_INTERVAL_SECONDS:-120}"
MAX_ITEMS="${COMPANYOS_FINANCIAL_QUEUE_MAX_ITEMS:-10}"

mkdir -p run logs
PIDFILE="run/financial_queue_worker.pid"
LOGFILE="logs/financial_queue_worker.log"

echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT INT TERM

echo "$(date -Iseconds) worker_start interval=$INTERVAL max_items=$MAX_ITEMS mode=dry_run" >> "$LOGFILE"

while true; do
  python - <<'PY' >> "$LOGFILE" 2>&1
from companyos.automatic_financial_queue_worker import run_once
r = run_once(max_items=int(__import__("os").getenv("COMPANYOS_FINANCIAL_QUEUE_MAX_ITEMS","10")))
print(r)
PY
  sleep "$INTERVAL"
done
