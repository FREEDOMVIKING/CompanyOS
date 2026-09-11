#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 34001-36000"
echo " INTEGRATED REAL EXECUTION CYCLE"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile   "$ROOT/scripts/companyos_integrated_cycle_demo.py"   "$ROOT/scripts/phase34001_36000_verify.py"

python "$ROOT/scripts/phase34001_36000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase34001_36000.py" --disable-warnings

echo
echo "PHASE34001_36000_INSTALL_OK"
echo "STAGE_ROUTER_TO_REAL_EXECUTOR=READY"
echo "VERIFIED_RECEIPTS_REQUIRED=TRUE"
echo "GOVERNANCE_ENFORCED=TRUE"
echo "TREASURY_GATE_PRESERVED=TRUE"
echo "LAUNCH_GATE_PRESERVED=TRUE"
echo "FALSE_COMPLETION_PREVENTION=READY"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_integrationops.sh demo"
echo "  bash ~/companyos/scripts/companyos_integrationops.sh status"
