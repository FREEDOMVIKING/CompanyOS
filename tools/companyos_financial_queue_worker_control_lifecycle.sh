#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
PIDFILE="run/financial_queue_worker.pid"
LOOP="$HOME/companyos/tools/companyos_financial_queue_worker_loop_lifecycle.sh"

is_live() {
  [ -f "$PIDFILE" ] || return 1
  PID="$(cat "$PIDFILE" 2>/dev/null || true)"
  [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null
}

case "${1:-status}" in
 start)
   if is_live; then echo "LIFECYCLE QUEUE WORKER: ALREADY LIVE PID=$(cat "$PIDFILE")"; exit 0; fi
   nohup "$LOOP" >/dev/null 2>&1 &
   sleep 1
   is_live && echo "LIFECYCLE QUEUE WORKER: LIVE PID=$(cat "$PIDFILE")" || exit 1
   ;;
 stop)
   if is_live; then kill "$(cat "$PIDFILE")" 2>/dev/null || true; sleep 1; fi
   rm -f "$PIDFILE"
   echo "LIFECYCLE QUEUE WORKER: STOPPED"
   ;;
 restart) "$0" stop; "$0" start ;;
 status)
   is_live && echo "LIFECYCLE QUEUE WORKER: LIVE PID=$(cat "$PIDFILE")" || echo "LIFECYCLE QUEUE WORKER: NOT LIVE"
   ;;
 *) echo "Usage: $0 {start|stop|restart|status}"; exit 2 ;;
esac
