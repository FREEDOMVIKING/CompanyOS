#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase8501_9000_liveintegration_$STAMP"

echo "=== CompanyOS Phase 8501-9000 ==="
echo "SECURE LIVE INTEGRATION RUNTIME"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase8501_9000_verify.py"
chmod +x "$ROOT/scripts/run_phase9000_live_integration_demo.py"
chmod +x "$ROOT/scripts/companyos_live_integration.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase8501_9000_verify.py
python -m pytest -q tests/test_phase8501_9000.py --disable-warnings

echo
echo "PHASE8501_9000_INSTALL_OK"
echo "CONNECTOR_CERTIFICATION=READY"
echo "LIVE_PREFLIGHT=READY"
echo "CREDENTIAL_READINESS=READY"
echo "ENDPOINT_POLICY=READY"
echo "LIVE_MODE_GATE=READY"
echo "REQUEST_SANITIZER=READY"
echo "RESPONSE_VALIDATOR=READY"
echo "PROVIDER_FAILOVER=READY"
echo "TRANSACTION_BOUNDARY=READY"
echo "CHANGE_WINDOW=READY"
echo "LIVE_OBSERVABILITY=READY"
echo "CONFIG_DRIFT_DETECTOR=READY"
echo "ROLLBACK_COORDINATOR=READY"
echo "PERSISTENT_LIVE_INTEGRATION_STATE=READY"
echo "LIVE_INTEGRATION_AUDIT=READY"
echo "CEO_LIVE_INTEGRATION_CONTROLLER=READY"
echo "Backup: $BACKUP"
