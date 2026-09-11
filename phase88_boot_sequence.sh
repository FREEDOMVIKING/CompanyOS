#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"

export PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos"

echo "=== COMPANYOS PHASE88 BOOT SEQUENCE ==="

python phase88_boot_readiness.py

echo "=== COMPANYOS BOOT READINESS: PASS ==="
echo "AUTONOMOUS_RUNTIME_START_ALLOWED=True"
echo "BROADCAST_PERFORMED_BY_BOOT_SEQUENCE=False"
