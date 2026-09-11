#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"
python "$ROOT/adaptive_keys_v18ctl" export >/dev/null
set +x
. "$ROOT/.companyos_secrets/adaptive_keys_v18.env"
echo "Adaptive connector credentials loaded without printing secret values."
