#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

PIDFILE="run/financial_queue_worker.pid"
LOOP="$HOME/companyos/tools/companyos_financial_queue_worker_loop_resource_aware.sh"

is_live() {
  [ -f "$PIDFILE" ] || return 1
  PID="$(cat "$PIDFILE" 2>/dev/null || true)"
  [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null
}

case "${1:-status}" in
  start)
    if is_live; then
      echo "RESOURCE-AWARE QUEUE WORKER: ALREADY LIVE PID=$(cat "$PIDFILE")"
      exit 0
    fi
    nohup "$LOOP" >/dev/null 2>&1 &
    sleep 1
    is_live && echo "RESOURCE-AWARE QUEUE WORKER: LIVE PID=$(cat "$PIDFILE")" || {
      echo "RESOURCE-AWARE QUEUE WORKER: FAILED TO START"; exit 1; }
    ;;
  stop)
    if is_live; then
      kill "$(cat "$PIDFILE")" 2>/dev/null || true
      sleep 1
    fi
    rm -f "$PIDFILE"
    echo "RESOURCE-AWARE QUEUE WORKER: STOPPED"
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  status)
    is_live && echo "RESOURCE-AWARE QUEUE WORKER: LIVE PID=$(cat "$PIDFILE")" || echo "RESOURCE-AWARE QUEUE WORKER: NOT LIVE"
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 2
    ;;
esac
