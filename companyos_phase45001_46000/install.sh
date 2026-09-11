#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
echo "======================================================"
echo " CompanyOS Phase 45001-46000"
echo " VERIFIED WALLET SOURCE INTEGRATION"
echo "======================================================"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }
mkdir -p "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"
chmod +x "$ROOT/scripts/"*.sh "$ROOT/scripts/"*.py 2>/dev/null || true
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python "$ROOT/scripts/phase45001_46000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase45001_46000.py" --disable-warnings
echo
echo "PHASE45001_46000_INSTALL_OK"
echo "VERIFIED_IDENTITY_LOADER=READY"
echo "PROPOSAL_SOURCE_INJECTION=READY"
echo "EXECUTION_SOURCE_GUARD=READY"
echo "PLACEHOLDER_SOURCE_REJECTION=READY"
echo "TREASURY_CONTROLS=PRESERVED"
echo "PREFLIGHT_CONTROLS=PRESERVED"
echo "RECEIPT_VERIFICATION=PRESERVED"
echo "LIVE_EXECUTION_AUTO_ENABLED=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_wallet_source.sh check"
echo "  bash ~/companyos/scripts/companyos_wallet_source.sh status"
