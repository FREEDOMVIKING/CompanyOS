#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"

echo "=== CompanyOS Live Provider Configuration ==="
echo
echo "This helper does NOT store your API key in a file."
echo "Export your key separately as COMPANYOS_CODER_API_KEY."
echo

: "${COMPANYOS_PROVIDER_ENDPOINT:?Set COMPANYOS_PROVIDER_ENDPOINT first}"
: "${COMPANYOS_PROVIDER_MODEL:?Set COMPANYOS_PROVIDER_MODEL first}"

export COMPANYOS_CODER_CMD="python $ROOT/scripts/companyos_http_coder_adapter.py"

cat > "$ROOT/.companyos_runtime/live_provider_env.example" <<EOF
export COMPANYOS_PROVIDER_ENDPOINT='${COMPANYOS_PROVIDER_ENDPOINT}'
export COMPANYOS_PROVIDER_MODEL='${COMPANYOS_PROVIDER_MODEL}'
export COMPANYOS_CODER_CMD='python $ROOT/scripts/companyos_http_coder_adapter.py'
# export COMPANYOS_CODER_API_KEY='set-secret-in-shell-only'
EOF

echo "COMPANYOS_CODER_CMD=$COMPANYOS_CODER_CMD"
echo "CONFIGURATION_HELPER_OK"
