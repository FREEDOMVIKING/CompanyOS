#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
INTERVAL="${COMPANYOS_DAEMON_INTERVAL:-60}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

mkdir -p "$ROOT/.companyos_runtime"
PIDFILE="$ROOT/.companyos_runtime/companyos_daemon.pid"
echo $$ > "$PIDFILE"

cleanup() {
  rm -f "$PIDFILE"
}
trap cleanup EXIT INT TERM

tick=0
while true; do
  tick=$((tick+1))
  python "$ROOT/scripts/run_phase15500_daemon_demo.py" >> "$ROOT/.companyos_runtime/companyos_daemon.log" 2>&1 || true
  sleep "$INTERVAL"
done
