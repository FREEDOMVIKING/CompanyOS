#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
ROOT="${HOME}/companyos"
SERVER_BIN="${ROOT}/local_ai/llama.cpp/build/bin/llama-server"
MODEL_PATH="${ROOT}/local_ai/models/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
RUN_DIR="${ROOT}/local_ai/run"
LOG_DIR="${ROOT}/logs"
HOST="${COMPANYOS_LOCAL_AI_HOST:-127.0.0.1}"
PORT="${COMPANYOS_LOCAL_AI_PORT:-8080}"
CTX="${COMPANYOS_LOCAL_AI_CONTEXT:-4096}"
THREADS="${COMPANYOS_LOCAL_AI_THREADS:-6}"
PARALLEL="${COMPANYOS_LOCAL_AI_PARALLEL:-1}"
mkdir -p "$RUN_DIR" "$LOG_DIR"
[[ -x "$SERVER_BIN" ]] || { echo LLAMA_SERVER_MISSING; exit 1; }
[[ -s "$MODEL_PATH" ]] || { echo LOCAL_MODEL_MISSING; exit 1; }
if curl -fsS "http://$HOST:$PORT/health" >/dev/null 2>&1; then echo "LOCAL_AI_ALREADY_READY http://$HOST:$PORT/v1"; exit 0; fi
if [[ -f "$RUN_DIR/llama-server.pid" ]]; then
  OLD_PID="$(cat "$RUN_DIR/llama-server.pid" 2>/dev/null || true)"
  [[ -n "$OLD_PID" ]] && kill "$OLD_PID" 2>/dev/null || true
  rm -f "$RUN_DIR/llama-server.pid"
fi
termux-wake-lock 2>/dev/null || true
ARGS=(--model "$MODEL_PATH" --host "$HOST" --port "$PORT" --ctx-size "$CTX" --threads "$THREADS" --parallel "$PARALLEL")
"$SERVER_BIN" --help 2>&1 | grep -q -- '--jinja' && ARGS+=(--jinja) || true
nohup "$SERVER_BIN" "${ARGS[@]}" > "$LOG_DIR/companyos_local_ai.log" 2>&1 &
PID=$!
echo "$PID" > "$RUN_DIR/llama-server.pid"
for _ in $(seq 1 150); do
  curl -fsS "http://$HOST:$PORT/health" >/dev/null 2>&1 && { echo "LOCAL_AI_READY http://$HOST:$PORT/v1"; exit 0; }
  kill -0 "$PID" 2>/dev/null || { echo LOCAL_AI_FAILED; tail -n 100 "$LOG_DIR/companyos_local_ai.log" || true; exit 1; }
  sleep 2
done
echo LOCAL_AI_START_TIMEOUT
tail -n 100 "$LOG_DIR/companyos_local_ai.log" || true
exit 1
