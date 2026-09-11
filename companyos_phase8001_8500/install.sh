#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase8001_8500_providerexec_$STAMP"

echo "=== CompanyOS Phase 8001-8500 ==="
echo "REAL PROVIDER EXECUTION ADAPTERS"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase8001_8500_verify.py"
chmod +x "$ROOT/scripts/run_phase8500_providerexec_demo.py"
chmod +x "$ROOT/scripts/companyos_providerexec.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase8001_8500_verify.py
python -m pytest -q tests/test_phase8001_8500.py --disable-warnings

echo
echo "PHASE8001_8500_INSTALL_OK"
echo "ADAPTER_CONTRACT=READY"
echo "ADAPTER_REGISTRY=READY"
echo "HTTP_ADAPTER=READY"
echo "COMMAND_ADAPTER=READY"
echo "SMTP_ADAPTER=READY"
echo "RESEARCH_ADAPTER=READY"
echo "DEPLOYMENT_ADAPTER=READY"
echo "FINANCE_READ_ADAPTER=READY"
echo "CREDENTIAL_CHECKER=READY"
echo "REQUEST_SIGNING_POLICY=READY"
echo "CIRCUIT_BREAKER=READY"
echo "QUOTA_MANAGER=READY"
echo "PROVIDER_EXECUTOR=READY"
echo "RECEIPT_VERIFIER=READY"
echo "APPROVAL_GATE=READY"
echo "PERSISTENT_PROVIDER_STATE=READY"
echo "PROVIDER_AUDIT=READY"
echo "CEO_PROVIDER_EXECUTION_CONTROLLER=READY"
echo "Backup: $BACKUP"
