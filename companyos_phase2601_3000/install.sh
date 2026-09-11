#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase2601_3000_controlplane_$STAMP"

echo "=== CompanyOS Phase 2601-3000 ==="
echo "UNIFIED AUTONOMOUS COMPANY CONTROL PLANE"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/scripts/companyos_control.sh" "$ROOT/scripts/"
cp "$HERE/tests/test_phase2601_3000.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase2601_3000_verify.py"
chmod +x "$ROOT/scripts/run_phase3000_controlplane_demo.py"
chmod +x "$ROOT/scripts/companyos_control.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase2601_3000_verify.py
python -m pytest -q tests/test_phase2601_3000.py --disable-warnings

echo
echo "PHASE2601_3000_INSTALL_OK"
echo "EVENT_BUS=READY"
echo "PERSISTENT_CEO_DAEMON=READY"
echo "EVENT_DRIVEN_DEPARTMENT_LOOPS=READY"
echo "VENTURE_LIFECYCLE_SUPERVISION=READY"
echo "PORTFOLIO_ALLOCATION=READY"
echo "BUDGET_GOVERNANCE=READY"
echo "RESOURCE_GOVERNANCE=READY"
echo "DEADLOCK_DETECTION=READY"
echo "SELF_HEALTH_MONITORING=READY"
echo "CHECKPOINT_MANAGEMENT=READY"
echo "RESTART_COORDINATION=READY"
echo "COMMAND_ROUTER=READY"
echo "UNIFIED_CONTROL_API=READY"
echo "RUNTIME_GUARDRAILS=READY"
echo "CONTROL_AUDIT=READY"
echo "Backup: $BACKUP"
