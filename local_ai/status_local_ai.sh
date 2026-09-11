#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
HOST="${COMPANYOS_LOCAL_AI_HOST:-127.0.0.1}"
PORT="${COMPANYOS_LOCAL_AI_PORT:-8080}"
if curl -fsS "http://$HOST:$PORT/health" >/dev/null 2>&1; then
  echo LOCAL_AI_HEALTHY
  curl -fsS "http://$HOST:$PORT/v1/models" | python -m json.tool 2>/dev/null || true
  exit 0
fi
echo LOCAL_AI_STOPPED_OR_UNHEALTHY
exit 1
