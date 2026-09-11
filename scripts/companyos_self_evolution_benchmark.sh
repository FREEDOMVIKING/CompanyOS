#!/data/data/com.termux/files/usr/bin/bash
ROOT="$HOME/companyos"
PIDFILE="$ROOT/.companyos_runtime/self_evolution_benchmark.pid"
LOGFILE="$ROOT/.companyos_runtime/self_evolution_benchmark.log"
INTERVAL="${COMPANYOS_SELF_EVOLUTION_BENCHMARK_INTERVAL_SECONDS:-600}"

mkdir -p "$ROOT/.companyos_runtime"

case "${1:-status}" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "SELF_EVOLUTION_BENCHMARK_RUNNING pid=$(cat "$PIDFILE")"
      exit 0
    fi
    nohup bash -c "
      cd '$ROOT' || exit 1
      export PYTHONPATH='$ROOT:$ROOT/companyos'
      while true; do
        python scripts/companyos_self_evolution_benchmark_once.py >> '$LOGFILE' 2>&1
        sleep '$INTERVAL'
      done
    " >/dev/null 2>&1 &
    echo $! > "$PIDFILE"
    echo "SELF_EVOLUTION_BENCHMARK_STARTED pid=$!"
    ;;
  stop)
    [ -f "$PIDFILE" ] && kill "$(cat "$PIDFILE")" 2>/dev/null || true
    rm -f "$PIDFILE"
    echo "SELF_EVOLUTION_BENCHMARK_STOPPED"
    ;;
  restart) "$0" stop; sleep 1; "$0" start ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "SELF_EVOLUTION_BENCHMARK_RUNNING pid=$(cat "$PIDFILE")"
    else
      echo "SELF_EVOLUTION_BENCHMARK_STOPPED"
    fi
    ;;
  once)
    cd "$ROOT" || exit 1
    export PYTHONPATH="$ROOT:$ROOT/companyos"
    python scripts/companyos_self_evolution_benchmark_once.py
    ;;
esac
