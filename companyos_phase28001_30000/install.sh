#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
echo "======================================================"
echo " CompanyOS Phase 28001-30000"
echo " AUTONOMOUS COMPANY OPERATING LOOP"
echo "======================================================"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }
mkdir -p "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"
chmod +x "$ROOT/scripts/"*.sh "$ROOT/scripts/"*.py 2>/dev/null || true
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python -m py_compile "$ROOT/scripts/companyos_autonomy_demo.py" "$ROOT/scripts/phase28001_30000_verify.py"
python "$ROOT/scripts/phase28001_30000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase28001_30000.py" --disable-warnings
echo
echo "PHASE28001_30000_INSTALL_OK"
echo "PERSISTENT_COMPANY_CYCLE=READY"
echo "DISCOVER_RESEARCH_SELECT_PLAN=READY"
echo "BUILD_TEST_OPERATE_FEEDBACK=READY"
echo "PORTFOLIO_LEARNING_LOOP=READY"
echo "AUTONOMY_GOVERNOR=READY"
echo "TREASURY_POLICY_ENFORCED=TRUE"
echo "IRREVERSIBLE_ACTIONS=APPROVAL_GATED"
echo "LIVE_MONEY_MOVEMENT_AUTO_ENABLED=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_autonomy.sh demo"
echo "  bash ~/companyos/scripts/companyos_autonomy.sh status"
