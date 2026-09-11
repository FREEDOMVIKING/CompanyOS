#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 50001-52000"
echo " CONTROLLED LIVE READINESS GATE"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"
chmod +x "$ROOT/scripts/"*.sh "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python "$ROOT/scripts/phase50001_52000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase50001_52000.py" --disable-warnings

echo
echo "PHASE50001_52000_INSTALL_OK"
echo "CONTROLLED_LIVE_READINESS_GATE=READY"
echo "ONE_SHOT_AUTHORIZATION=READY"
echo "TTL_EXPIRATION=READY"
echo "AMOUNT_CAP=READY"
echo "DESTINATION_LOCK=READY"
echo "SINGLE_USE=READY"
echo "TREASURY_CONTROLS=PRESERVED"
echo "KILL_SWITCH=PRESERVED"
echo "RECEIPT_VERIFICATION=REQUIRED"
echo "AUTONOMOUS_LIVE_ENABLED=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_livegate.sh readiness"
echo "  bash ~/companyos/scripts/companyos_livegate.sh status"
