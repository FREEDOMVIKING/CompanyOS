#!/data/data/com.termux/files/usr/bin/bash
set -u
cd "$HOME/companyos" || exit 1
INTERVAL="${COMPANYOS_RESEARCH_INTERVAL_SECONDS:-600}"
PIDFILE="run/external_research_network.pid"
LOGFILE="logs/external_research_network.log"
mkdir -p run logs
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT INT TERM
echo "$(date -Iseconds) external_research_worker_start interval=$INTERVAL mode=read_only" >> "$LOGFILE"
while true; do
  python tools/companyos_external_research_once.py >> "$LOGFILE" 2>&1
  sleep "$INTERVAL"
done
