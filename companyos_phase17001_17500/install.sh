#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase17001_17500_$STAMP"

echo "=============================================="
echo " CompanyOS Phase 17001-17500"
echo " SPECIALIST CAPABILITY EXPANSION"
echo "=============================================="

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"

if [ -f "$ROOT/companyos/workerops/execution_bridge.py" ]; then
  cp "$ROOT/companyos/workerops/execution_bridge.py" "$BACKUP/execution_bridge.py"
fi

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

cp "$HERE/scripts/execution_bridge_phase17500.py"    "$ROOT/companyos/workerops/execution_bridge.py"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile   "$ROOT/companyos/workerops/execution_bridge.py"   "$ROOT/scripts/phase17001_17500_verify.py"

python "$ROOT/scripts/phase17001_17500_verify.py"
python -m pytest -q "$ROOT/tests/test_phase17001_17500.py" --disable-warnings

echo
echo "PHASE17001_17500_INSTALL_OK"
echo "RESEARCH_SPECIALIST=READY"
echo "FINANCE_SPECIALIST=READY"
echo "PRODUCT_SPECIALIST=READY"
echo "GROWTH_SPECIALIST=READY"
echo "OPERATIONS_SPECIALIST=READY"
echo "CUSTOMER_SUCCESS_SPECIALIST=READY"
echo "LIVE_AI_SPECIALIST_ROUTING=READY"
echo "APPROVAL_BOUNDARIES=PRESERVED"
echo "Backup: $BACKUP"
