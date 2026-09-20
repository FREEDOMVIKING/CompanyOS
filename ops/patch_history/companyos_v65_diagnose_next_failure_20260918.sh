#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V65 NEXT-FAILURE DIAGNOSTIC ====="
echo "HEAD=$(git rev-parse HEAD)"
echo "BRANCH=$(git branch --show-current)"
git status --short
echo "===== CAPABILITY EXPORT SMOKE ====="
python - <<'PY'
from companyos.capabilityops import CapabilityPolicy, CapabilityRegistry, RealExecutionBridge
print("CAPABILITY_EXPORTS=PASS")
PY
echo "===== PHASE 16001-16500 ====="
python -m pytest -q tests/test_phase16001_16500.py --disable-warnings --maxfail=1
echo "===== FULL SUITE: STOP ON NEXT FAILURE ====="
python -m pytest -q tests --disable-warnings --maxfail=1
echo "V65_FULL_SUITE=PASS"
