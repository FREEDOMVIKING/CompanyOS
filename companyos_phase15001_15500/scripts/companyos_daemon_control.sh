#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
PIDFILE="$ROOT/.companyos_runtime/companyos_daemon.pid"
LOGFILE="$ROOT/.companyos_runtime/companyos_daemon.log"

case "${1:-status}" in
  start)
    mkdir -p "$ROOT/.companyos_runtime"
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "COMPANYOS_DAEMON_ALREADY_RUNNING pid=$(cat "$PIDFILE")"
      exit 0
    fi
    nohup bash "$ROOT/scripts/companyos_daemon_forever.sh" >/dev/null 2>&1 &
    sleep 1
    if [ -f "$PIDFILE" ]; then
      echo "COMPANYOS_DAEMON_STARTED pid=$(cat "$PIDFILE")"
    else
      echo "COMPANYOS_DAEMON_START_FAILED"
      exit 1
    fi
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      PID="$(cat "$PIDFILE")"
      kill "$PID" 2>/dev/null || true
      rm -f "$PIDFILE"
      echo "COMPANYOS_DAEMON_STOPPED"
    else
      echo "COMPANYOS_DAEMON_NOT_RUNNING"
    fi
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "COMPANYOS_DAEMON_RUNNING pid=$(cat "$PIDFILE")"
    else
      echo "COMPANYOS_DAEMON_STOPPED"
    fi
    ;;
  logs)
    tail -n 80 "$LOGFILE" 2>/dev/null || true
    ;;
  *)
    echo "Usage: $0 {start|stop|status|logs}"
    exit 2
    ;;
esac
