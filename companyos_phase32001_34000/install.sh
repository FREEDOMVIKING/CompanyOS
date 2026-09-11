#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 32001-34000"
echo " REAL CAPABILITY EXECUTION + VERIFIED RECEIPTS"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile   "$ROOT/scripts/companyos_execution_scan.py"   "$ROOT/scripts/companyos_execution_demo.py"   "$ROOT/scripts/phase32001_34000_verify.py"

python "$ROOT/scripts/phase32001_34000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase32001_34000.py" --disable-warnings

echo
echo "PHASE32001_34000_INSTALL_OK"
echo "DYNAMIC_CAPABILITY_DISCOVERY=READY"
echo "REAL_MODULE_EXECUTION=READY"
echo "FALLBACK_DISCOVERY=READY"
echo "EXECUTION_RECEIPTS=READY"
echo "POST_EXECUTION_VERIFICATION=READY"
echo "FALSE_COMPLETION_PREVENTION=READY"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_executionops.sh scan"
echo "  bash ~/companyos/scripts/companyos_executionops.sh demo"
echo "  bash ~/companyos/scripts/companyos_executionops.sh status"
