#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase9501_10000_production_runtime_$STAMP"

echo "=== CompanyOS Phase 9501-10000 ==="
echo "AUTONOMOUS COMPANY PRODUCTION RUNTIME"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase9501_10000_verify.py"
chmod +x "$ROOT/scripts/run_phase10000_production_runtime_demo.py"
chmod +x "$ROOT/scripts/companyos_production.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase9501_10000_verify.py
python -m pytest -q tests/test_phase9501_10000.py --disable-warnings

echo
echo "PHASE9501_10000_INSTALL_OK"
echo "RUNTIME_PROFILE=READY"
echo "STARTUP_PREFLIGHT=READY"
echo "SERVICE_GRAPH=READY"
echo "PRODUCTION_SUPERVISOR=READY"
echo "CONTINUOUS_COMPANY_CYCLE=READY"
echo "PRODUCTION_SCHEDULER=READY"
echo "MISSION_ROUTER=READY"
echo "APPROVAL_BRIDGE=READY"
echo "CHECKPOINT_CHAIN=READY"
echo "PRODUCTION_RECOVERY_MANAGER=READY"
echo "PRODUCTION_OBSERVABILITY=READY"
echo "PRODUCTION_READINESS_GATE=READY"
echo "PERSISTENT_RUNTIME_STATE=READY"
echo "PRODUCTION_RUNTIME_AUDIT=READY"
echo "CEO_PRODUCTION_RUNTIME=READY"
echo "Backup: $BACKUP"
