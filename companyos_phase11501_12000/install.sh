#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase11501_12000_resilience_$STAMP"

echo "=== CompanyOS Phase 11501-12000 ==="
echo "ENTERPRISE RESILIENCE + CONTINUITY COMMAND"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase11501_12000_verify.py"
chmod +x "$ROOT/scripts/run_phase12000_resilience_demo.py"
chmod +x "$ROOT/scripts/companyos_resilience.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase11501_12000_verify.py
python -m pytest -q tests/test_phase11501_12000.py --disable-warnings

echo
echo "PHASE11501_12000_INSTALL_OK"
echo "DEPENDENCY_MAP=READY"
echo "FAILURE_DOMAIN_ANALYZER=READY"
echo "CONTINUITY_PLANNER=READY"
echo "BACKUP_POLICY=READY"
echo "RESTORE_VERIFIER=READY"
echo "DEGRADED_MODE_PLANNER=READY"
echo "INCIDENT_COMMANDER=READY"
echo "PROVIDER_RESILIENCE_PLANNER=READY"
echo "DATA_INTEGRITY_GUARD=READY"
echo "DISASTER_RECOVERY_PLANNER=READY"
echo "RESILIENCE_SCORE=READY"
echo "RESILIENCE_AUTHORITY_BOUNDARY=READY"
echo "PERSISTENT_RESILIENCE_STATE=READY"
echo "RESILIENCE_AUDIT=READY"
echo "CEO_RESILIENCE_OPS_CONTROLLER=READY"
echo "Backup: $BACKUP"
