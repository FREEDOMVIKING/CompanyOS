#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"
python "$ROOT/adaptive_resolver_v18ctl" runtime-env >/dev/null
set +x
. "$ROOT/.companyos_secrets/adaptive_runtime_v18.env"
echo "Adaptive CompanyOS connector credentials loaded without printing secret values."
