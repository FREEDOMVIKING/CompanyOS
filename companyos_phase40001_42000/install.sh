#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 40001-42000"
echo " EXISTING WALLET AUTOBIND + SOLANA PREFLIGHT"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile   "$ROOT/scripts/companyos_wallet_autobind.py"   "$ROOT/scripts/companyos_solana_preflight.py"   "$ROOT/scripts/phase40001_42000_verify.py"

python "$ROOT/scripts/phase40001_42000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase40001_42000.py" --disable-warnings

echo
echo "PHASE40001_42000_INSTALL_OK"
echo "EXISTING_WALLET_AUTODISCOVERY=READY"
echo "BINDING_METADATA_GENERATION=READY"
echo "PRIVATE_KEY_MATERIAL_COPIED=FALSE"
echo "SOLANA_RPC_PREFLIGHT=READY"
echo "SIGNER_PRESENCE_VALIDATION=READY"
echo "BROADCAST_ATTEMPTED_DURING_PREFLIGHT=FALSE"
echo "LIVE_EXECUTION_AUTO_ENABLED=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_wallet_autobind.sh scan"
echo "  bash ~/companyos/scripts/companyos_wallet_autobind.sh bind"
echo "  bash ~/companyos/scripts/companyos_wallet_autobind.sh preflight"
echo "  bash ~/companyos/scripts/companyos_wallet_execution.sh readiness"
