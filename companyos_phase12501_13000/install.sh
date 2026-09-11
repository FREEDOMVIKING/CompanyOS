#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"; HERE="$(cd "$(dirname "$0")" && pwd)"; STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase12501_13000_revenue_$STAMP"
echo "=== CompanyOS Phase 12501-13000 ==="
echo "AUTONOMOUS REVENUE + GROWTH COMMAND"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"; cp "$HERE/scripts/"* "$ROOT/scripts/"; cp "$HERE/tests/"* "$ROOT/tests/"
chmod +x "$ROOT/scripts/phase12501_13000_verify.py" "$ROOT/scripts/run_phase13000_revenue_demo.py" "$ROOT/scripts/companyos_revenue.sh"
cd "$ROOT"; export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python scripts/phase12501_13000_verify.py
python -m pytest -q tests/test_phase12501_13000.py --disable-warnings
echo
echo "PHASE12501_13000_INSTALL_OK"
echo "MARKET_SIGNAL_ENGINE=READY"
echo "OFFER_OPTIMIZER=READY"
echo "PRICING_EXPERIMENT_ENGINE=READY"
echo "REVENUE_PIPELINE_ENGINE=READY"
echo "RETENTION_ENGINE=READY"
echo "UNIT_ECONOMICS_ENGINE=READY"
echo "REVENUE_FORECAST_ENGINE=READY"
echo "GROWTH_ALLOCATOR=READY"
echo "GROWTH_EXPERIMENT_ENGINE=READY"
echo "CUSTOMER_VALUE_ENGINE=READY"
echo "REVENUE_AUTHORITY_BOUNDARY=READY"
echo "PERSISTENT_REVENUE_STATE=READY"
echo "REVENUE_AUDIT=READY"
echo "CEO_REVENUE_OPS_CONTROLLER=READY"
echo "Backup: $BACKUP"
