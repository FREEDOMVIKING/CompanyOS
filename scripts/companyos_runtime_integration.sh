#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
RUNTIME="$ROOT/.companyos_runtime"
PIDFILE="$RUNTIME/integrated_runtime.pid"
LOGFILE="$RUNTIME/integrated_runtime.log"

mkdir -p "$RUNTIME"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  start)
    if [ -f "$ROOT/.companyos_runtime/live_intelligence.env" ]; then
      source "$ROOT/.companyos_runtime/live_intelligence.env"
    fi
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "INTEGRATED_RUNTIME_ALREADY_RUNNING pid=$(cat "$PIDFILE")"
      exit 0
    fi
    nohup python "$ROOT/scripts/companyos_integrated_runtime.py"       --interval "${COMPANYOS_AUTONOMY_INTERVAL:-300}"       >>"$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 2
    echo "INTEGRATED_RUNTIME_STARTED pid=$(cat "$PIDFILE")"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      kill "$(cat "$PIDFILE")" 2>/dev/null || true
      rm -f "$PIDFILE"
    fi
    pkill -f "companyos_integrated_runtime.py" 2>/dev/null || true
    echo "INTEGRATED_RUNTIME_STOPPED"
    ;;
  restart)
    "$0" stop
    sleep 1
    "$0" start
    ;;
  once)
    python "$ROOT/scripts/companyos_integrated_runtime.py" --once
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "INTEGRATED_RUNTIME_RUNNING pid=$(cat "$PIDFILE")"
    else
      echo "INTEGRATED_RUNTIME_STOPPED"
    fi
    ;;
  logs)
    tail -n 150 "$LOGFILE" 2>/dev/null || true
    ;;
  checkpoint)
    cat "$RUNTIME/autonomy_checkpoint.json" 2>/dev/null || echo "NO_CHECKPOINT"
    ;;
  verify)
    python "$ROOT/scripts/phase36001_38000_verify.py"
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|once|status|logs|checkpoint|verify}"
    exit 2
    ;;
esac
