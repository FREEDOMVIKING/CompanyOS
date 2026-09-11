#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
RUNTIME="$ROOT/.companyos_runtime"
PIDFILE="$RUNTIME/reasoning_gateway.pid"
LOGFILE="$RUNTIME/reasoning_gateway.log"
LIVE_ENV="$RUNTIME/live_intelligence.env"

mkdir -p "$RUNTIME"

load_env() {
  if [ -f "$LIVE_ENV" ]; then
    # shellcheck disable=SC1090
    source "$LIVE_ENV"
  fi

  export COMPANYOS_REASONING_URL="${COMPANYOS_REASONING_URL:-http://127.0.0.1:8765/reason}"
  export COMPANYOS_PROVIDER_URL="${COMPANYOS_PROVIDER_URL:-https://openrouter.ai/api/v1/chat/completions}"
  export COMPANYOS_PROVIDER_MODEL="${COMPANYOS_PROVIDER_MODEL:-${COMPANYOS_OPENROUTER_MODEL:-openrouter/auto}}"

  if [ -z "${COMPANYOS_PROVIDER_API_KEY:-}" ] && [ -n "${OPENROUTER_API_KEY:-}" ]; then
    export COMPANYOS_PROVIDER_API_KEY="$OPENROUTER_API_KEY"
  fi
}

case "${1:-status}" in
  start)
    load_env
    if [ -z "${COMPANYOS_PROVIDER_API_KEY:-}" ]; then
      echo "ERROR: No provider API key loaded. Load OPENROUTER_API_KEY/live_intelligence.env first."
      exit 1
    fi

    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "REASONING_GATEWAY_ALREADY_RUNNING pid=$(cat "$PIDFILE")"
      exit 0
    fi

    pkill -f "companyos_reasoning_gateway.py" 2>/dev/null || true
    nohup python "$ROOT/scripts/companyos_reasoning_gateway.py" >>"$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 2

    if kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "REASONING_GATEWAY_STARTED pid=$(cat "$PIDFILE")"
    else
      echo "REASONING_GATEWAY_START_FAILED"
      tail -n 40 "$LOGFILE" 2>/dev/null || true
      exit 1
    fi
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      kill "$(cat "$PIDFILE")" 2>/dev/null || true
      rm -f "$PIDFILE"
    fi
    pkill -f "companyos_reasoning_gateway.py" 2>/dev/null || true
    echo "REASONING_GATEWAY_STOPPED"
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
      echo "REASONING_GATEWAY_RUNNING pid=$(cat "$PIDFILE")"
    else
      echo "REASONING_GATEWAY_STOPPED"
    fi
    ;;
  test)
    curl -sS -X POST http://127.0.0.1:8765/reason \
      -H "Content-Type: application/json" \
      -d '{"messages":[{"role":"user","content":"Reply with exactly: COMPANYOS_REASONING_ONLINE"}]}'
    echo
    ;;
  logs)
    tail -n 80 "$LOGFILE" 2>/dev/null || true
    ;;
  *)
    echo "Usage: $0 {start|stop|status|test|logs}"
    exit 2
    ;;
esac
