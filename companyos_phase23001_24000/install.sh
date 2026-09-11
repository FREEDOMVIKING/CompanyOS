#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 23001-24000"
echo " EXISTING CRYPTO WALLET CONNECTOR"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile \
  "$ROOT/scripts/companyos_wallet_scan.py" \
  "$ROOT/scripts/companyos_crypto_bind.py" \
  "$ROOT/scripts/companyos_crypto_payments.py"

python "$ROOT/scripts/phase23001_24000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase23001_24000.py" --disable-warnings

echo
echo "PHASE23001_24000_INSTALL_OK"
echo "EXISTING_WALLET_DISCOVERY=READY"
echo "EXISTING_WALLET_ADAPTER=READY"
echo "TREASURY_POLICY_BRIDGE=READY"
echo "DESTINATION_ALLOWLIST=READY"
echo "PRIVATE_KEYS_EMBEDDED=FALSE"
echo "LIVE_TRANSFER_ENABLED_BY_DEFAULT=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_crypto.sh scan"
echo "  bash ~/companyos/scripts/companyos_crypto.sh bind"
echo "  bash ~/companyos/scripts/companyos_crypto.sh status"
