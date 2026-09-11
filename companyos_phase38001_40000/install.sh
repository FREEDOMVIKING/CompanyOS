#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 38001-40000"
echo " WALLET EXECUTION WIRING + TREASURY CONTROL"
echo "======================================================"

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

python -m py_compile   "$ROOT/scripts/companyos_wallet_execution_readiness.py"   "$ROOT/scripts/phase38001_40000_verify.py"

python "$ROOT/scripts/phase38001_40000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase38001_40000.py" --disable-warnings

echo
echo "PHASE38001_40000_INSTALL_OK"
echo "EXISTING_WALLET_REUSE=READY"
echo "SOLANA_RPC_READINESS=READY"
echo "ISOLATED_SIGNER_REUSE=READY"
echo "TREASURY_GATE=MANDATORY"
echo "PREFLIGHT_REQUIRED=TRUE"
echo "IDEMPOTENCY_REQUIRED=TRUE"
echo "FINANCIAL_KILL_SWITCH=READY"
echo "ONCHAIN_RECEIPT_VERIFICATION=READY"
echo "LIVE_EXECUTION_AUTO_ENABLED=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_wallet_execution.sh readiness"
echo "  bash ~/companyos/scripts/companyos_wallet_execution.sh status"
