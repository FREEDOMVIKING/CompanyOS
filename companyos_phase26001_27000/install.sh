#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 26001-27000"
echo " AUTONOMOUS CEO FINANCIAL DECISION LOOP"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile   "$ROOT/scripts/companyos_ceo_finance_demo.py"   "$ROOT/scripts/phase26001_27000_verify.py"

python "$ROOT/scripts/phase26001_27000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase26001_27000.py" --disable-warnings

echo
echo "PHASE26001_27000_INSTALL_OK"
echo "FINANCIAL_PLANNER=READY"
echo "EXPECTED_VALUE_ENGINE=READY"
echo "CAPITAL_ALLOCATOR=READY"
echo "TREASURY_AUTHORIZATION_BRIDGE=READY"
echo "HARD_TREASURY_LIMITS_EXTERNAL_TO_AI=TRUE"
echo "LIVE_EXECUTION_AUTO_ENABLED=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_ceo_finops.sh demo"
echo "  bash ~/companyos/scripts/companyos_ceo_finops.sh status"
