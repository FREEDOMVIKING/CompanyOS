#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
RUNTIME="$ROOT/.companyos_runtime"
mkdir -p "$RUNTIME"

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  echo "ERROR: OPENROUTER_API_KEY is not loaded."
  exit 1
fi

cat > "$RUNTIME/live_intelligence.env" <<EOF
export COMPANYOS_CODER_CMD='python $ROOT/scripts/companyos_openrouter_coder.py'
export COMPANYOS_OPENROUTER_MODEL='${COMPANYOS_OPENROUTER_MODEL:-openrouter/auto-beta}'
export COMPANYOS_MAX_MODEL_CALLS_PER_MISSION='${COMPANYOS_MAX_MODEL_CALLS_PER_MISSION:-8}'
export COMPANYOS_MAX_REPAIR_ATTEMPTS='${COMPANYOS_MAX_REPAIR_ATTEMPTS:-5}'
export COMPANYOS_MODEL_TIMEOUT_SECONDS='${COMPANYOS_MODEL_TIMEOUT_SECONDS:-600}'
EOF

export COMPANYOS_CODER_CMD="python $ROOT/scripts/companyos_openrouter_coder.py"
export COMPANYOS_OPENROUTER_MODEL="${COMPANYOS_OPENROUTER_MODEL:-openrouter/auto-beta}"

echo "LIVE_INTELLIGENCE_ACTIVATED=TRUE"
echo "COMPANYOS_CODER_CMD=$COMPANYOS_CODER_CMD"
echo "COMPANYOS_OPENROUTER_MODEL=$COMPANYOS_OPENROUTER_MODEL"
echo "RUNTIME_ENV=$RUNTIME/live_intelligence.env"
echo "For future shells: source '$RUNTIME/live_intelligence.env'"
