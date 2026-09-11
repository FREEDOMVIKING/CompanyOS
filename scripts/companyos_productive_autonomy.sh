#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos"
mkdir -p .companyos_runtime

PIDFILE=.companyos_runtime/productive_autonomy_watchdog.pid
LOGFILE=.companyos_runtime/productive_autonomy_watchdog.log
STATE=.companyos_runtime/productive_autonomy_watchdog_state.json

cmd="${1:-status}"

case "$cmd" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "PRODUCTIVE_AUTONOMY_ALREADY_RUNNING pid=$(cat "$PIDFILE")"
      exit 0
    fi
    nohup python companyos/runtime/productive_autonomy_watchdog.py >> "$LOGFILE" 2>&1 &
    pid=$!
    echo "$pid" > "$PIDFILE"
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
      echo "PRODUCTIVE_AUTONOMY_STARTED pid=$pid"
    else
      echo "PRODUCTIVE_AUTONOMY_START_FAILED"
      tail -n 100 "$LOGFILE" || true
      exit 1
    fi
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      pid="$(cat "$PIDFILE" 2>/dev/null || true)"
      if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" || true
        sleep 1
      fi
      rm -f "$PIDFILE"
    fi
    echo "PRODUCTIVE_AUTONOMY_STOPPED"
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "PRODUCTIVE_AUTONOMY_RUNNING pid=$(cat "$PIDFILE")"
    else
      echo "PRODUCTIVE_AUTONOMY_STOPPED"
    fi
    [ -f "$STATE" ] && cat "$STATE" || true
    ;;
  logs)
    tail -n 200 -f "$LOGFILE"
    ;;
  once)
    python - <<'PY'
from companyos.runtime.productive_autonomy_watchdog import tick
import json
print(json.dumps(tick(), indent=2, default=str))
PY
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs|once}"
    exit 2
    ;;
esac
