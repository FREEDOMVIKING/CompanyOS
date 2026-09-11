#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
RUNTIME="$ROOT/companyos_runtime/canonical_daemon"
PIDFILE="$RUNTIME/daemon.pid"
LOGDIR="$RUNTIME/logs"
LOGFILE="$LOGDIR/companyos.log"
PYTHON="${PYTHON:-python}"

mkdir -p "$RUNTIME" "$LOGDIR"
export PYTHONPATH="$ROOT:$ROOT/companyos"

is_running() {
  [ -f "$PIDFILE" ] || return 1
  local pid
  pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  [ -n "$pid" ] || return 1
  kill -0 "$pid" 2>/dev/null
}

cleanup_stale_pid() {
  if [ -f "$PIDFILE" ] && ! is_running; then
    rm -f "$PIDFILE"
  fi
}

rotate_log() {
  if [ -f "$LOGFILE" ]; then
    local size
    size="$(wc -c < "$LOGFILE" 2>/dev/null || echo 0)"
    if [ "${size:-0}" -gt 5242880 ]; then
      mv "$LOGFILE" "$LOGFILE.1"
    fi
  fi
}

start_service() {
  cleanup_stale_pid
  if is_running; then
    echo "COMPANYOS_SERVICE_ALREADY_RUNNING pid=$(cat "$PIDFILE")"
    return 0
  fi

  rotate_log
  nohup "$PYTHON" "$ROOT/scripts/companyos_canonical_daemon.py" \
    --heartbeat-interval 15 \
    >>"$LOGFILE" 2>&1 &

  local child=$!
  sleep 3

  if [ -f "$PIDFILE" ] && is_running; then
    echo "COMPANYOS_SERVICE_STARTED pid=$(cat "$PIDFILE")"
    return 0
  fi

  echo "COMPANYOS_SERVICE_START_FAILED child=$child"
  tail -80 "$LOGFILE" 2>/dev/null || true
  return 1
}

stop_service() {
  cleanup_stale_pid
  if ! is_running; then
    echo "COMPANYOS_SERVICE_NOT_RUNNING"
    return 0
  fi

  local pid
  pid="$(cat "$PIDFILE")"
  kill -TERM "$pid" 2>/dev/null || true

  local i=0
  while kill -0 "$pid" 2>/dev/null && [ "$i" -lt 20 ]; do
    sleep 1
    i=$((i+1))
  done

  if kill -0 "$pid" 2>/dev/null; then
    kill -KILL "$pid" 2>/dev/null || true
    sleep 1
  fi

  rm -f "$PIDFILE"
  echo "COMPANYOS_SERVICE_STOPPED"
}

status_service() {
  cleanup_stale_pid
  if is_running; then
    echo "COMPANYOS_SERVICE_RUNNING pid=$(cat "$PIDFILE")"
  else
    echo "COMPANYOS_SERVICE_STOPPED"
  fi

  if [ -f "$RUNTIME/heartbeat.json" ]; then
    cat "$RUNTIME/heartbeat.json"
  fi
}

case "${1:-}" in
  start) start_service ;;
  stop) stop_service ;;
  restart) stop_service; sleep 2; start_service ;;
  status) status_service ;;
  logs) tail -120 "$LOGFILE" 2>/dev/null || true ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs}"
    exit 2
    ;;
esac
