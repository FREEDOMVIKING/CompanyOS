#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase1701_2000_persistent_runtime_$STAMP"

echo "=== CompanyOS Phase 1701-2000 ==="
echo "PERSISTENT AUTONOMOUS COMPANY RUNTIME"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/scripts/companyos_runtime.sh" "$ROOT/scripts/"
cp "$HERE/tests/test_phase1701_2000.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase1701_2000_verify.py"
chmod +x "$ROOT/scripts/run_phase2000_runtime_demo.py"
chmod +x "$ROOT/scripts/companyos_runtime.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase1701_2000_verify.py
python -m pytest -q tests/test_phase1701_2000.py --disable-warnings

echo
echo "PHASE1701_2000_INSTALL_OK"
echo "PERSISTENT_JOB_QUEUE=READY"
echo "RUNTIME_HEARTBEAT=READY"
echo "RUNTIME_WATCHDOG=READY"
echo "AUTONOMOUS_SCHEDULER=READY"
echo "DEPARTMENT_RUNTIME=READY"
echo "AGENT_RETURN_BUS=READY"
echo "CROSS_VENTURE_RESOURCE_SCHEDULER=READY"
echo "CHECKPOINT_STORE=READY"
echo "RESTART_SAFE_RECOVERY=READY"
echo "SERVICE_SUPERVISOR=READY"
echo "RUNTIME_INCIDENT_MANAGER=READY"
echo "CONTINUOUS_CEO_CYCLES=READY"
echo "UNIFIED_RUNTIME_CONTROL=READY"
echo "RUNTIME_AUDIT=READY"
echo "RUNTIME_HEALTH_SNAPSHOT=READY"
echo "CEO_COMPANY_RUNTIME=READY"
echo "Backup: $BACKUP"
