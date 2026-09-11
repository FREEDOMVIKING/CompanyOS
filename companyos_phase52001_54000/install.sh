#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 52001-54000"
echo " CONTROLLED EXECUTION ORCHESTRATOR"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"
chmod +x "$ROOT/scripts/"*.sh "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python "$ROOT/scripts/phase52001_54000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase52001_54000.py" --disable-warnings

echo
echo "PHASE52001_54000_INSTALL_OK"
echo "CONTROLLED_EXECUTION_ORCHESTRATOR=READY"
echo "LIVE_READINESS_GATE=REQUIRED"
echo "ONE_SHOT_AUTHORIZATION=REQUIRED"
echo "TRANSACTION_LIFECYCLE=REQUIRED"
echo "TREASURY_CONTROLS=REQUIRED"
echo "DUPLICATE_GUARD=REQUIRED"
echo "KILL_SWITCH=REQUIRED"
echo "EXECUTION_RECEIPTS=READY"
echo "POST_EXECUTION_LOCKOUT=READY"
echo "BROADCAST_ADAPTER_INTEGRATION_READY=FALSE"
echo "AUTONOMOUS_LIVE_ENABLED=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_controlledexec.sh demo"
echo "  bash ~/companyos/scripts/companyos_controlledexec.sh status"
