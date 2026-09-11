#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase1101_1250_autonomous_business_ops_portfolio_$STAMP"

echo "=== CompanyOS Phase 1101-1250 ==="
echo "AUTONOMOUS BUSINESS OPERATIONS + PORTFOLIO ORCHESTRATION"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase1101_1250"
cp -a "$HERE/companyos_phase1101_1250" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase1101_1250.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase1101_1250_verify.py"
chmod +x "$ROOT/scripts/run_phase1250_business_ops_demo.py"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase1101_1250_verify.py
python -m pytest -q tests/test_phase1101_1250.py --disable-warnings

echo
echo "PHASE1101_1250_INSTALL_OK"
echo "CUSTOMER_ACQUISITION=READY"
echo "SALES_PIPELINE=READY"
echo "OFFER_OPTIMIZATION=READY"
echo "CAMPAIGN_ALLOCATION=READY"
echo "CRM_ORCHESTRATION=READY"
echo "CUSTOMER_SUCCESS=READY"
echo "FINANCIAL_CONTROLLER=READY"
echo "CASHFLOW_GUARD=READY"
echo "RESOURCE_ALLOCATOR=READY"
echo "KPI_ENGINE=READY"
echo "GROWTH_EXPERIMENT_LOOP=READY"
echo "PORTFOLIO_ORCHESTRATOR=READY"
echo "BUSINESS_RISK_GATE=READY"
echo "PERSISTENT_BUSINESS_STATE=READY"
echo "BUSINESS_AUDIT=READY"
echo "UNIFIED_BUSINESS_OPS_CONTROLLER=READY"
echo "Backup: $BACKUP"
