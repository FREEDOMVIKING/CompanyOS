#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase3001_3500_execution_fabric_$STAMP"

echo "=== CompanyOS Phase 3001-3500 ==="
echo "AUTONOMOUS RUNTIME EXECUTION FABRIC"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/scripts/companyos_execution.sh" "$ROOT/scripts/"
cp "$HERE/tests/test_phase3001_3500.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase3001_3500_verify.py"
chmod +x "$ROOT/scripts/run_phase3500_execution_demo.py"
chmod +x "$ROOT/scripts/companyos_execution.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase3001_3500_verify.py
python -m pytest -q tests/test_phase3001_3500.py --disable-warnings

echo
echo "PHASE3001_3500_INSTALL_OK"
echo "PERSISTENT_WORKER_POOL=READY"
echo "JOB_DISPATCH=READY"
echo "CROSS_DEPARTMENT_WORKFLOW_RUNTIME=READY"
echo "VENTURE_SPAWNING=READY"
echo "LONG_RUNNING_SERVICE_SUPERVISION=READY"
echo "ADAPTIVE_RETRY_ENGINE=READY"
echo "DEEP_RECOVERY_COORDINATION=READY"
echo "BACKPRESSURE_CONTROL=READY"
echo "JOB_LEASING=READY"
echo "EXECUTION_CHECKPOINTING=READY"
echo "LONG_RUNNING_SCHEDULER=READY"
echo "EXECUTION_METRICS=READY"
echo "EXECUTION_GUARDRAILS=READY"
echo "EXECUTION_AUDIT=READY"
echo "CEO_EXECUTION_FABRIC=READY"
echo "Backup: $BACKUP"
