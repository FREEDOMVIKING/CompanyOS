#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 30001-32000"
echo " REAL CAPABILITY WIRING + CONTROLLED AUTONOMY"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile   "$ROOT/scripts/companyos_capability_scan.py"   "$ROOT/scripts/companyos_capability_demo.py"   "$ROOT/scripts/phase30001_32000_verify.py"

python "$ROOT/scripts/phase30001_32000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase30001_32000.py" --disable-warnings

echo
echo "PHASE30001_32000_INSTALL_OK"
echo "STAGE_TO_CAPABILITY_ROUTER=READY"
echo "CONTROLLED_AUTONOMY_POLICY=READY"
echo "REAL_CAPABILITY_EXECUTION_PLANNING=READY"
echo "ROUTINE_REVERSIBLE_ACTIONS=AUTO_ALLOWED"
echo "HIGH_IMPACT_IRREVERSIBLE_ACTIONS=APPROVAL_GATED"
echo "TREASURY_HARD_LIMITS=PRESERVED"
echo "CREDENTIAL_CHANGES=APPROVAL_GATED"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_capabilityops.sh scan"
echo "  bash ~/companyos/scripts/companyos_capabilityops.sh demo"
echo "  bash ~/companyos/scripts/companyos_capabilityops.sh status"
