#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$HOME/companyos:$HOME/companyos/src${PYTHONPATH:+:$PYTHONPATH}"

mkdir -p "$HOME/companyos/.companyos_runtime"

nohup python "$HOME/companyos/scripts/run_ceo_service.py"   > "$HOME/companyos/.companyos_runtime/ceo_service.out"   2> "$HOME/companyos/.companyos_runtime/ceo_service.err" &

echo $! > "$HOME/companyos/.companyos_runtime/ceo_service.pid"

echo "COMPANYOS_CEO_SERVICE_STARTED"
echo "PID=$(cat "$HOME/companyos/.companyos_runtime/ceo_service.pid")"
echo "LOG=$HOME/companyos/.companyos_runtime/ceo_service.out"
