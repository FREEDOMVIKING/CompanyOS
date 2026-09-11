#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "========================================================"
echo " CompanyOS Phase 24001-25000"
echo " TREASURY-GATED MULTICHAIN EXECUTION"
echo "========================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }
[ -f "$ROOT/agents/multichain_execution_adapter.py" ] || {
  echo "ERROR: existing multichain adapter not found"
  exit 1
}

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile \
  "$ROOT/scripts/companyos_multichain_money.py" \
  "$ROOT/scripts/phase24001_25000_verify.py"

python "$ROOT/scripts/phase24001_25000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase24001_25000.py" --disable-warnings

echo
echo "PHASE24001_25000_INSTALL_OK"
echo "EXISTING_MULTICHAIN_ADAPTER_BRIDGE=READY"
echo "SOLANA_ROUTE=READY"
echo "EVM_ROUTE=READY"
echo "BITCOIN_ROUTE=READY"
echo "TREASURY_GATE=MANDATORY"
echo "FINANCIAL_KILL_SWITCH=READY"
echo "IDEMPOTENCY=READY"
echo "RECEIPT_STORE=READY"
echo "DRY_RUN_DEFAULT=TRUE"
echo "LIVE_EXECUTION_DEFAULT=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_money.sh readiness"
echo "  bash ~/companyos/scripts/companyos_money.sh status"
