#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 48001-50000"
echo " SOLANA NON-BROADCAST SIMULATION"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"
chmod +x "$ROOT/scripts/"*.sh "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python "$ROOT/scripts/phase48001_50000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase48001_50000.py" --disable-warnings

echo
echo "PHASE48001_50000_INSTALL_OK"
echo "VERIFIED_IDENTITY_REQUIRED=TRUE"
echo "RPC_BLOCKHASH_CHECK=READY"
echo "BALANCE_CHECK=READY"
echo "SIMULATION_GATE=READY"
echo "SIGNED_TX_SIMULATION_SUPPORTED=TRUE"
echo "BROADCAST_ATTEMPTED=FALSE"
echo "LIVE_EXECUTION_AUTO_ENABLED=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_solanasim.sh run"
echo "  bash ~/companyos/scripts/companyos_solanasim.sh status"
