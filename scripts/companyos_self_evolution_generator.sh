#!/data/data/com.termux/files/usr/bin/bash
ROOT="$HOME/companyos"
PID="$ROOT/.companyos_runtime/self_evolution_generator.pid"
LOG="$ROOT/.companyos_runtime/self_evolution_generator.log"
INTERVAL="${COMPANYOS_SELF_EVOLUTION_GENERATOR_INTERVAL_SECONDS:-900}"
mkdir -p "$ROOT/.companyos_runtime"
case "${1:-status}" in
 start)
  if [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; then echo "SELF_EVOLUTION_GENERATOR_RUNNING pid=$(cat "$PID")"; exit 0; fi
  nohup bash -c "cd '$ROOT'; export PYTHONPATH='$ROOT:$ROOT/companyos'; while true; do python scripts/companyos_self_evolution_full_cycle.py >> '$LOG' 2>&1; sleep '$INTERVAL'; done" >/dev/null 2>&1 &
  echo $! > "$PID"; echo "SELF_EVOLUTION_GENERATOR_STARTED pid=$!";;
 stop) [ -f "$PID" ] && kill "$(cat "$PID")" 2>/dev/null || true; rm -f "$PID"; echo "SELF_EVOLUTION_GENERATOR_STOPPED";;
 restart) "$0" stop; sleep 1; "$0" start;;
 status) if [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; then echo "SELF_EVOLUTION_GENERATOR_RUNNING pid=$(cat "$PID")"; else echo "SELF_EVOLUTION_GENERATOR_STOPPED"; fi;;
 once) cd "$ROOT"; export PYTHONPATH="$ROOT:$ROOT/companyos"; python scripts/companyos_self_evolution_full_cycle.py;;
esac
