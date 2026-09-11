#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase4501_5000_scale_ops_$STAMP"

echo "=== CompanyOS Phase 4501-5000 ==="
echo "AUTONOMOUS FINANCE + COMPLIANCE + SCALE"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase4501_5000_verify.py"
chmod +x "$ROOT/scripts/run_phase5000_scale_ops_demo.py"
chmod +x "$ROOT/scripts/companyos_scale_ops.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase4501_5000_verify.py
python -m pytest -q tests/test_phase4501_5000.py --disable-warnings

echo
echo "PHASE4501_5000_INSTALL_OK"
echo "FINANCIAL_PLANNING=READY"
echo "CASHFLOW_ENGINE=READY"
echo "RUNWAY_MANAGEMENT=READY"
echo "SCALE_ALLOCATOR=READY"
echo "VENDOR_MANAGEMENT=READY"
echo "COMPLIANCE_REGISTRY=READY"
echo "RISK_REGISTER=READY"
echo "GOVERNANCE_ENGINE=READY"
echo "SCENARIO_PLANNING=READY"
echo "CAPITAL_EFFICIENCY=READY"
echo "PORTFOLIO_REBALANCING=READY"
echo "APPROVAL_MATRIX=READY"
echo "PERSISTENT_SCALE_STATE=READY"
echo "SCALE_AUDIT=READY"
echo "CEO_SCALE_OPS_CONTROLLER=READY"
echo "Backup: $BACKUP"
