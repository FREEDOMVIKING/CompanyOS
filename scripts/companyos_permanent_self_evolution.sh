#!/data/data/com.termux/files/usr/bin/bash
ROOT="$HOME/companyos"
PIDFILE="$ROOT/.companyos_runtime/permanent_self_evolution.pid"
LOGFILE="$ROOT/.companyos_runtime/permanent_self_evolution.log"
INTERVAL="${COMPANYOS_PERMANENT_EVOLUTION_INTERVAL_SECONDS:-300}"

mkdir -p "$ROOT/.companyos_runtime"

case "${1:-status}" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "PERMANENT_SELF_EVOLUTION_RUNNING pid=$(cat "$PIDFILE")"
      exit 0
    fi
    nohup bash -c "
      cd '$ROOT' || exit 1
      export PYTHONPATH='$ROOT:$ROOT/companyos'
      while true; do
        python scripts/companyos_permanent_self_evolution_once.py >> '$LOGFILE' 2>&1
        sleep '$INTERVAL'
      done
    " >/dev/null 2>&1 &
    echo $! > "$PIDFILE"
    echo "PERMANENT_SELF_EVOLUTION_STARTED pid=$!"
    ;;
  stop)
    [ -f "$PIDFILE" ] && kill "$(cat "$PIDFILE")" 2>/dev/null || true
    rm -f "$PIDFILE"
    echo "PERMANENT_SELF_EVOLUTION_STOPPED"
    ;;
  restart) "$0" stop; sleep 1; "$0" start ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "PERMANENT_SELF_EVOLUTION_RUNNING pid=$(cat "$PIDFILE")"
    else
      echo "PERMANENT_SELF_EVOLUTION_STOPPED"
    fi
    ;;
  once)
    cd "$ROOT" || exit 1
    export PYTHONPATH="$ROOT:$ROOT/companyos"
    python scripts/companyos_permanent_self_evolution_once.py
    ;;
esac
