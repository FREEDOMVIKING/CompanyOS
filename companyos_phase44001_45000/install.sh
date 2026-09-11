#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 44001-45000"
echo " SIGNER COMPATIBILITY BRIDGE"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile   "$ROOT/scripts/companyos_signer_compat.py"   "$ROOT/scripts/phase44001_45000_verify.py"

python "$ROOT/scripts/phase44001_45000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase44001_45000.py" --disable-warnings

echo
echo "PHASE44001_45000_INSTALL_OK"
echo "SIGNER_CONTRACT_DETECTION=READY"
echo "JSON_STDIN_BRIDGE=READY"
echo "SANITIZED_DIAGNOSTICS=READY"
echo "COMPATIBLE_REQUEST_SELECTION=READY"
echo "BROADCAST_DISABLED=TRUE"
echo "LIVE_EXECUTION_AUTO_ENABLED=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_signercompat.sh probe"
echo "  bash ~/companyos/scripts/companyos_signercompat.sh report"
echo "  bash ~/companyos/scripts/companyos_signercompat.sh status"
