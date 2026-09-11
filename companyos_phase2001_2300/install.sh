#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase2001_2300_real_world_integration_orchestration_$STAMP"

echo "=== CompanyOS Phase 2001-2300 ==="
echo "REAL-WORLD INTEGRATION + AUTONOMOUS ORCHESTRATION"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase2001_2300.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase2001_2300_verify.py"
chmod +x "$ROOT/scripts/run_phase2300_integration_demo.py"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase2001_2300_verify.py
python -m pytest -q tests/test_phase2001_2300.py --disable-warnings

echo
echo "PHASE2001_2300_INSTALL_OK"
echo "INTEGRATION_REGISTRY=READY"
echo "CREDENTIAL_REFERENCE_VAULT=READY"
echo "DYNAMIC_TOOL_ROUTING=READY"
echo "DEPARTMENT_ROUTING=READY"
echo "PARALLEL_SPECIALIST_DISPATCH=READY"
echo "SPECIALIST_RETURN_BUS=READY"
echo "EXTERNAL_ACTION_APPROVAL_GATE=READY"
echo "RESULT_VERIFICATION=READY"
echo "PROVIDER_HEALTH_RANKING=READY"
echo "CONNECTOR_POLICY=READY"
echo "EXTERNAL_WORKFLOW_ENGINE=READY"
echo "COMMUNICATION_ORCHESTRATOR=READY"
echo "DEPLOYMENT_BRIDGE=READY"
echo "SCHEDULED_WORK_PLANNER=READY"
echo "EXECUTION_LEDGER=READY"
echo "CEO_INTEGRATION_CONTROLLER=READY"
echo "Backup: $BACKUP"
