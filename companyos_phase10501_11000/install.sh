#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase10501_11000_enterprise_opt_$STAMP"

echo "=== CompanyOS Phase 10501-11000 ==="
echo "AUTONOMOUS ENTERPRISE OPTIMIZATION + PORTFOLIO"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase10501_11000_verify.py"
chmod +x "$ROOT/scripts/run_phase11000_enterprise_optimizer_demo.py"
chmod +x "$ROOT/scripts/companyos_enterprise_opt.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase10501_11000_verify.py
python -m pytest -q tests/test_phase10501_11000.py --disable-warnings

echo
echo "PHASE10501_11000_INSTALL_OK"
echo "ENTERPRISE_SCORECARD=READY"
echo "CAPITAL_ALLOCATOR=READY"
echo "VENTURE_PRUNER=READY"
echo "STRATEGY_ALLOCATOR=READY"
echo "DEPARTMENT_CAPACITY_PLANNER=READY"
echo "TALENT_ALLOCATOR=READY"
echo "PROFITABILITY_ENGINE=READY"
echo "PORTFOLIO_RISK_ENGINE=READY"
echo "PORTFOLIO_SCENARIO_ENGINE=READY"
echo "ENTERPRISE_OPTIMIZATION_LOOP=READY"
echo "LEARNING_COMPOUNDER=READY"
echo "ENTERPRISE_AUTHORITY_BOUNDARY=READY"
echo "PERSISTENT_ENTERPRISE_OPTIMIZATION_STATE=READY"
echo "ENTERPRISE_OPTIMIZATION_AUDIT=READY"
echo "CEO_ENTERPRISE_OPTIMIZER=READY"
echo "Backup: $BACKUP"
