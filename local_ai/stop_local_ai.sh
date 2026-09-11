#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
PID_FILE="${HOME}/companyos/local_ai/run/llama-server.pid"
if [[ -f "$PID_FILE" ]]; then
  PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  [[ -n "$PID" ]] && kill "$PID" 2>/dev/null || true
  sleep 2
  [[ -n "$PID" ]] && kill -9 "$PID" 2>/dev/null || true
  rm -f "$PID_FILE"
fi
termux-wake-unlock 2>/dev/null || true
echo LOCAL_AI_STOPPED
