#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 42001-44000"
echo " WALLET SIGNER END-TO-END VALIDATION"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile   "$ROOT/scripts/companyos_signer_validation.py"   "$ROOT/scripts/phase42001_44000_verify.py"

python "$ROOT/scripts/phase42001_44000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase42001_44000.py" --disable-warnings

echo
echo "PHASE42001_44000_INSTALL_OK"
echo "SIGNER_PROBE=READY"
echo "UNSIGNED_SOLANA_INTENT_BUILDER=READY"
echo "LOCAL_SIGNATURE_STRUCTURE_CHECK=READY"
echo "SOLANA_SIMULATION_SUPPORT=READY"
echo "BROADCAST_DISABLED_DURING_VALIDATION=TRUE"
echo "READY_FOR_LIVE_AUTO_ENABLED=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_signervalidation.sh validate"
echo "  bash ~/companyos/scripts/companyos_signervalidation.sh report"
echo "  bash ~/companyos/scripts/companyos_signervalidation.sh status"
