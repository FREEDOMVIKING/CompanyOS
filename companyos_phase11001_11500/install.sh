#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase11001_11500_expansion_$STAMP"

echo "=== CompanyOS Phase 11001-11500 ==="
echo "AUTONOMOUS MULTI-VENTURE EXPANSION"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase11001_11500_verify.py"
chmod +x "$ROOT/scripts/run_phase11500_expansion_demo.py"
chmod +x "$ROOT/scripts/companyos_expansion.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase11001_11500_verify.py
python -m pytest -q tests/test_phase11001_11500.py --disable-warnings

echo
echo "PHASE11001_11500_INSTALL_OK"
echo "EXPANSION_RADAR=READY"
echo "MARKET_ENTRY_PLANNER=READY"
echo "VENTURE_REPLICATION_ENGINE=READY"
echo "SHARED_SERVICES_ALLOCATOR=READY"
echo "CROSS_VENTURE_SALES_ENGINE=READY"
echo "CROSS_SELL_ENGINE=READY"
echo "REGIONALIZATION_PLANNER=READY"
echo "PARTNER_OPPORTUNITY_ENGINE=READY"
echo "PORTFOLIO_SYNERGY_ENGINE=READY"
echo "EXPANSION_RISK_ENGINE=READY"
echo "EXPANSION_SEQUENCER=READY"
echo "EXPANSION_AUTHORITY_BOUNDARY=READY"
echo "PERSISTENT_EXPANSION_STATE=READY"
echo "EXPANSION_AUDIT=READY"
echo "CEO_EXPANSION_OPS_CONTROLLER=READY"
echo "Backup: $BACKUP"
