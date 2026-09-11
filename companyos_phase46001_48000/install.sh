#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 46001-48000"
echo " NON-BROADCAST TRANSACTION LIFECYCLE"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python "$ROOT/scripts/phase46001_48000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase46001_48000.py" --disable-warnings

echo
echo "PHASE46001_48000_INSTALL_OK"
echo "VERIFIED_WALLET_SOURCE=READY"
echo "TRANSACTION_POLICY=READY"
echo "BALANCE_AND_FEE_GUARD=READY"
echo "DUPLICATE_PAYMENT_GUARD=READY"
echo "FINANCIAL_KILL_SWITCH=ENFORCED"
echo "NONBROADCAST_VALIDATION=READY"
echo "SIGNING_AUTO_ENABLED=FALSE"
echo "BROADCAST_AUTO_ENABLED=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_transactionops.sh demo"
echo "  bash ~/companyos/scripts/companyos_transactionops.sh status"
