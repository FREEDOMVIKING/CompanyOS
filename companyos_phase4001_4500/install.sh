#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase4001_4500_market_ops_$STAMP"

echo "=== CompanyOS Phase 4001-4500 ==="
echo "AUTONOMOUS MARKET EXECUTION + GROWTH"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase4001_4500_verify.py"
chmod +x "$ROOT/scripts/run_phase4500_market_ops_demo.py"
chmod +x "$ROOT/scripts/companyos_market_ops.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase4001_4500_verify.py
python -m pytest -q tests/test_phase4001_4500.py --disable-warnings

echo
echo "PHASE4001_4500_INSTALL_OK"
echo "MARKET_SIGNAL_ENGINE=READY"
echo "CUSTOMER_DISCOVERY=READY"
echo "CHANNEL_OPTIMIZER=READY"
echo "PRICING_ENGINE=READY"
echo "SALES_ORCHESTRATOR=READY"
echo "AUTONOMOUS_GROWTH_LOOP=READY"
echo "RETENTION_ENGINE=READY"
echo "REVENUE_OPTIMIZER=READY"
echo "EXPERIMENT_PORTFOLIO=READY"
echo "MARKET_FEEDBACK_LOOP=READY"
echo "MARKET_OPS_GUARDRAILS=READY"
echo "MARKET_OPS_STATE=READY"
echo "MARKET_OPS_AUDIT=READY"
echo "CEO_MARKET_OPS_CONTROLLER=READY"
echo "Backup: $BACKUP"
