#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase2301_2600_persistent_autonomous_operations_$STAMP"

echo "=== CompanyOS Phase 2301-2600 ==="
echo "PERSISTENT AUTONOMOUS OPERATIONS + CONTINUOUS OPTIMIZATION"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase2301_2600.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase2301_2600_verify.py"
chmod +x "$ROOT/scripts/run_phase2600_operations_demo.py"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase2301_2600_verify.py
python -m pytest -q tests/test_phase2301_2600.py --disable-warnings

echo
echo "PHASE2301_2600_INSTALL_OK"
echo "PERSISTENT_GOAL_TRACKING=READY"
echo "MEMORY_CONSOLIDATION=READY"
echo "BACKGROUND_SCHEDULING=READY"
echo "CROSS_DEPARTMENT_COORDINATION=READY"
echo "CONTINUOUS_BUSINESS_OPTIMIZATION=READY"
echo "PERSISTENT_FAILURE_RECOVERY=READY"
echo "ORGANIZATIONAL_LEARNING=READY"
echo "OPERATING_METRICS=READY"
echo "INITIATIVE_MANAGEMENT=READY"
echo "OPERATING_POLICY_ENGINE=READY"
echo "CONTINUOUS_CYCLE_STATE=READY"
echo "OPERATIONS_AUDIT=READY"
echo "CEO_OPERATIONS_CONTROLLER=READY"
echo "Backup: $BACKUP"
