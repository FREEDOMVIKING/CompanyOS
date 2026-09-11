#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 27001-28000"
echo " AUTONOMOUS BUSINESS EXECUTION + REVENUE LOOP"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile   "$ROOT/scripts/companyos_business_demo.py"   "$ROOT/scripts/phase27001_28000_verify.py"

python "$ROOT/scripts/phase27001_28000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase27001_28000.py" --disable-warnings

echo
echo "PHASE27001_28000_INSTALL_OK"
echo "VENTURE_SELECTION=READY"
echo "LAUNCH_GATE=READY"
echo "REVENUE_TRACKING=READY"
echo "PORTFOLIO_FEEDBACK=READY"
echo "REINVESTMENT_DECISIONING=READY"
echo "IRREVERSIBLE_ACTIONS=APPROVAL_GATED"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_businessops.sh demo"
echo "  bash ~/companyos/scripts/companyos_businessops.sh status"
