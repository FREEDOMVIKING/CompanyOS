#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase1451_1700_self_managing_ai_org_$STAMP"

echo "=== CompanyOS Phase 1451-1700 ==="
echo "SELF-MANAGING AI ORGANIZATION"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp -r "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase1451_1700.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase1451_1700_verify.py"
chmod +x "$ROOT/scripts/run_phase1700_self_managing_org_demo.py"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase1451_1700_verify.py
python -m pytest -q tests/test_phase1451_1700.py --disable-warnings

echo
echo "PHASE1451_1700_INSTALL_OK"
echo "PERSISTENT_EXECUTIVE_LOOP=READY"
echo "GOAL_DECOMPOSITION=READY"
echo "PLANNING_HORIZONS=READY"
echo "DEPARTMENT_TASK_MARKET=READY"
echo "DYNAMIC_AGENT_STAFFING=READY"
echo "AGENT_PERFORMANCE_MANAGEMENT=READY"
echo "BUDGET_ARBITRATION=READY"
echo "RESOURCE_CONFLICT_RESOLUTION=READY"
echo "VENTURE_COORDINATION=READY"
echo "FAILURE_RECOVERY=READY"
echo "APPROVAL_ROUTING=READY"
echo "DAILY_WEEKLY_MONTHLY_CADENCE=READY"
echo "DECISION_MEMORY=READY"
echo "ORGANIZATION_STATE=READY"
echo "ORGANIZATION_AUDIT=READY"
echo "Backup: $BACKUP"
