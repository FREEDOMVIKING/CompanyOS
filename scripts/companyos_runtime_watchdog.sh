#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/companyos"
cd "$ROOT" || exit 1

RUNTIME="$ROOT/.companyos_runtime"
LOG="$RUNTIME/continuous_runtime.log"
PIDFILE="$RUNTIME/continuous_runtime.pid"
mkdir -p "$RUNTIME"

start_runtime() {
  if [ -f "$PIDFILE" ]; then
    OLD="$(cat "$PIDFILE" 2>/dev/null || true)"
    if [ -n "${OLD:-}" ] && kill -0 "$OLD" 2>/dev/null; then
      echo "CompanyOS runtime already running with PID $OLD"
      return 0
    fi
  fi

  rm -f "$RUNTIME/continuous_runtime.stop"
  nohup python "$ROOT/scripts/companyos_continuous_runtime.py" run >>"$LOG" 2>&1 &
  PID=$!
  echo "$PID" > "$PIDFILE"
  echo "CompanyOS runtime started: PID $PID"
  echo "Log: $LOG"
}

stop_runtime() {
  python "$ROOT/scripts/companyos_continuous_runtime.py" stop >/dev/null 2>&1 || true
  if [ -f "$PIDFILE" ]; then
    PID="$(cat "$PIDFILE" 2>/dev/null || true)"
    if [ -n "${PID:-}" ] && kill -0 "$PID" 2>/dev/null; then
      for _ in 1 2 3 4 5 6; do
        kill -0 "$PID" 2>/dev/null || break
        sleep 2
      done
      kill -0 "$PID" 2>/dev/null && kill "$PID" 2>/dev/null || true
    fi
    rm -f "$PIDFILE"
  fi
  echo "CompanyOS runtime stop requested."
}

case "${1:-status}" in
  start) start_runtime ;;
  stop) stop_runtime ;;
  restart) stop_runtime; sleep 2; start_runtime ;;
  status)
    python "$ROOT/scripts/companyos_continuous_runtime.py" status | python -m json.tool
    ;;
  once)
    python "$ROOT/scripts/companyos_continuous_runtime.py" once | python -m json.tool
    ;;
  logs)
    tail -n 120 "$LOG"
    ;;
  reconcile)
    python "$ROOT/scripts/companyos_continuous_runtime.py" reconcile | python -m json.tool
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|once|logs|reconcile}"
    exit 2
    ;;
esac
