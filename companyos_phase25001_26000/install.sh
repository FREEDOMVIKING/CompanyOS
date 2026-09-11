#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 25001-26000"
echo " AUTONOMOUS FINANCIAL OPS + END-TO-END SAFETY"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }
[ -f "$ROOT/agents/multichain_execution_adapter.py" ] || {
  echo "ERROR: existing multichain adapter missing"
  exit 1
}

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile   "$ROOT/scripts/companyos_financial_e2e.py"   "$ROOT/scripts/phase25001_26000_verify.py"

python "$ROOT/scripts/phase25001_26000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase25001_26000.py" --disable-warnings

echo
echo "PHASE25001_26000_INSTALL_OK"
echo "FINANCIAL_INTENT_SCHEMA=READY"
echo "END_TO_END_DRY_RUN=READY"
echo "TREASURY_POLICY_VALIDATION=READY"
echo "IDEMPOTENCY_VALIDATION=READY"
echo "ACTIVATION_GATE=READY"
echo "LIVE_EXECUTION_AUTOMATIC_ENABLE=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_finops.sh status"
echo "  bash ~/companyos/scripts/companyos_money.sh readiness"
echo
echo "Then run an end-to-end DRY RUN using an address already present in your allowlist:"
echo "  python ~/companyos/scripts/companyos_financial_e2e.py --chain solana --amount 1 --balance 1000 --destination YOUR_ALLOWLISTED_ADDRESS"
