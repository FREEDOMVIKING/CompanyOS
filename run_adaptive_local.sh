#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
cd "${HOME}/companyos"
set -a
source .env
set +a
export PYTHONPATH="${HOME}/companyos/scripts${PYTHONPATH:+:$PYTHONPATH}"
./local_ai/start_local_ai.sh >/dev/null
python scripts/companyos_adaptive_self_build.py run
