#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 22001-23000"
echo " POLICY-ENFORCED FINANCIAL EXECUTION FRAMEWORK"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile   "$ROOT/scripts/companyos_payment_demo.py"   "$ROOT/scripts/phase22001_23000_verify.py"

python "$ROOT/scripts/phase22001_23000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase22001_23000.py" --disable-warnings

echo
echo "PHASE22001_23000_INSTALL_OK"
echo "PAYMENT_CONNECTOR_REGISTRY=READY"
echo "SANDBOX_PAYMENT_CONNECTOR=READY"
echo "POLICY_ENFORCEMENT=READY"
echo "APPROVAL_QUEUE=READY"
echo "IDEMPOTENCY=READY"
echo "LEDGER_RECORDING=READY"
echo "RECONCILIATION=READY"
echo "REAL_PROVIDER_CONNECTED=FALSE"
echo "REAL_MONEY_ENABLED=FALSE"
