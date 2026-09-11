#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase7001_7500_connectors_$STAMP"

echo "=== CompanyOS Phase 7001-7500 ==="
echo "REAL-WORLD CONNECTOR + CAPABILITY LAYER"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase7001_7500_verify.py"
chmod +x "$ROOT/scripts/run_phase7500_connector_demo.py"
chmod +x "$ROOT/scripts/companyos_connectors.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase7001_7500_verify.py
python -m pytest -q tests/test_phase7001_7500.py --disable-warnings

echo
echo "PHASE7001_7500_INSTALL_OK"
echo "CONNECTOR_REGISTRY=READY"
echo "CREDENTIAL_REFERENCE_STORE=READY"
echo "CONNECTOR_HEALTH_ROUTER=READY"
echo "CAPABILITY_DISCOVERY=READY"
echo "RESEARCH_ADAPTER=READY"
echo "COMMUNICATION_ADAPTER=READY"
echo "DEPLOYMENT_ADAPTER=READY"
echo "FINANCE_ADAPTER=READY"
echo "GENERIC_API_ADAPTER=READY"
echo "CONNECTOR_APPROVAL_ROUTER=READY"
echo "FALLBACK_ENGINE=READY"
echo "EXECUTION_RECEIPTS=READY"
echo "PERSISTENT_CONNECTOR_STATE=READY"
echo "CONNECTOR_AUDIT=READY"
echo "CEO_CONNECTOR_CONTROLLER=READY"
echo "Backup: $BACKUP"
