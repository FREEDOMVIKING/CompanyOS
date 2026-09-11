#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
HOST="${COMPANYOS_LOCAL_AI_HOST:-127.0.0.1}"
PORT="${COMPANYOS_LOCAL_AI_PORT:-8080}"
OUT="${HOME}/companyos/local_ai/run/last_test.json"
curl -fsS "http://$HOST:$PORT/v1/chat/completions" -H 'Content-Type: application/json' -H 'Authorization: Bearer companyos-local' -d '{"model":"companyos-local","temperature":0,"max_tokens":80,"messages":[{"role":"system","content":"Follow the requested response format exactly."},{"role":"user","content":"Reply with exactly COMPANYOS_LOCAL_AI_PASS"}]}' > "$OUT"
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos/local_ai/run/last_test.json"
d=json.loads(p.read_text())
t=d["choices"][0]["message"]["content"].strip()
print("MODEL_REPLY:",t)
if "COMPANYOS_LOCAL_AI_PASS" not in t: raise SystemExit("LOCAL_AI_RESPONSE_CHECK_FAILED")
print("LOCAL_AI_INFERENCE PASS")
PY
