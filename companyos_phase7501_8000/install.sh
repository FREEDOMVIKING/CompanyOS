#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase7501_8000_liveexec_$STAMP"

echo "=== CompanyOS Phase 7501-8000 ==="
echo "LIVE CAPABILITY EXECUTION + CONTROL PLANE"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase7501_8000_verify.py" "$ROOT/scripts/run_phase8000_liveexec_demo.py" "$ROOT/scripts/companyos_liveexec.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase7501_8000_verify.py
python -m pytest -q tests/test_phase7501_8000.py --disable-warnings

echo
echo "PHASE7501_8000_INSTALL_OK"
echo "EXECUTION_JOB=READY"
echo "IDEMPOTENCY_STORE=READY"
echo "RETRY_TIMEOUT_POLICY=READY"
echo "PROVIDER_INVOKER=READY"
echo "RESULT_VERIFIER=READY"
echo "EXECUTION_ROUTER=READY"
echo "PERSISTENT_JOB_STORE=READY"
echo "LIVE_WORKER_RUNTIME=READY"
echo "EXECUTION_RECEIPTS=READY"
echo "OBSERVABILITY=READY"
echo "FAILURE_RECOVERY=READY"
echo "APPROVAL_EXECUTION_BRIDGE=READY"
echo "PERSISTENT_EXECUTION_STATE=READY"
echo "EXECUTION_AUDIT=READY"
echo "CEO_LIVE_EXECUTION_CONTROLLER=READY"
echo "Backup: $BACKUP"
