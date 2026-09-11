#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
RUNTIME="$ROOT/.companyos_runtime"
PIDFILE="$RUNTIME/autonomy_daemon.pid"
LOGFILE="$RUNTIME/autonomy_daemon.log"
mkdir -p "$RUNTIME"

case "${1:-status}" in
  start)
    if [ -f "$ROOT/.companyos_runtime/live_intelligence.env" ]; then
      source "$ROOT/.companyos_runtime/live_intelligence.env"
    fi
    export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "AUTONOMY_DAEMON_ALREADY_RUNNING pid=$(cat "$PIDFILE")"
      exit 0
    fi

    nohup python "$ROOT/scripts/companyos_runtime_daemon.py" --interval "${COMPANYOS_AUTONOMY_INTERVAL:-300}"       >>"$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 2
    echo "AUTONOMY_DAEMON_STARTED pid=$(cat "$PIDFILE")"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      kill "$(cat "$PIDFILE")" 2>/dev/null || true
      rm -f "$PIDFILE"
    fi
    pkill -f "companyos_runtime_daemon.py" 2>/dev/null || true
    echo "AUTONOMY_DAEMON_STOPPED"
    ;;
  restart)
    "$0" stop
    sleep 1
    "$0" start
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "AUTONOMY_DAEMON_RUNNING pid=$(cat "$PIDFILE")"
    else
      echo "AUTONOMY_DAEMON_STOPPED"
    fi
    ;;
  logs)
    tail -n 120 "$LOGFILE" 2>/dev/null || true
    ;;
  checkpoint)
    cat "$RUNTIME/autonomy_checkpoint.json" 2>/dev/null || echo "NO_CHECKPOINT"
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs|checkpoint}"
    exit 2
    ;;
esac
