#!/data/data/com.termux/files/usr/bin/bash
set -u
cd "$HOME/companyos" || exit 1

# Load only CompanyOS financial live-control variables from .env.
# Secrets are exported to child processes but never printed.
if [ -f "$HOME/companyos/.env" ]; then
    while IFS='=' read -r key value; do
        key="${key//[[:space:]]/}"
        case "$key" in
            COMPANYOS_AUTONOMOUS_FINANCIAL_MODE|COMPANYOS_LIVE_CONFIRM_TOKEN)
                value="${value%$'\r'}"
                value="${value#\"}"
                value="${value%\"}"
                value="${value#\'}"
                value="${value%\'}"
                export "$key=$value"
                ;;
        esac
    done < "$HOME/companyos/.env"
fi


INTERVAL="${COMPANYOS_FINANCIAL_QUEUE_INTERVAL_SECONDS:-120}"
mkdir -p run logs
PIDFILE="run/financial_queue_worker.pid"
LOGFILE="logs/financial_queue_worker.log"

echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT INT TERM
echo "$(date -Iseconds) lifecycle_worker_start interval=$INTERVAL mode=${COMPANYOS_AUTONOMOUS_FINANCIAL_MODE:-dry_run}" >> "$LOGFILE"

while true; do
  python tools/companyos_financial_lifecycle_worker_once.py >> "$LOGFILE" 2>&1
  sleep "$INTERVAL"
done
