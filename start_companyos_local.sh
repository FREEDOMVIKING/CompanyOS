#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
cd "${HOME}/companyos"
set -a
[[ -f .env ]] && source .env
set +a
./local_ai/start_local_ai.sh
./local_ai/status_local_ai.sh
echo "Adaptive build: python scripts/companyos_adaptive_self_build.py run"
