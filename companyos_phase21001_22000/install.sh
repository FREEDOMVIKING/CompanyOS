#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 21001-22000"
echo " PERSISTENT AUTONOMY + TREASURY SAFETY KERNEL"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile   "$ROOT/scripts/companyos_runtime_daemon.py"   "$ROOT/scripts/phase21001_22000_verify.py"

python "$ROOT/scripts/phase21001_22000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase21001_22000.py" --disable-warnings

echo
echo "PHASE21001_22000_INSTALL_OK"
echo "PERSISTENT_AUTONOMY_DAEMON=READY"
echo "CHECKPOINTING=READY"
echo "CRASH_RESTART_CONTROLS=READY"
echo "TREASURY_POLICY_ENGINE=READY"
echo "ALLOWLIST=READY"
echo "RESERVE_FLOOR=READY"
echo "DAILY_LIMITS=READY"
echo "LOSS_LIMIT=READY"
echo "LEDGER_AND_RECONCILIATION=READY"
echo "AUTONOMOUS_MONEY_MOVEMENT=DISABLED_BY_DEFAULT"
echo
echo "Start daemon:"
echo "  bash ~/companyos/scripts/companyos_runtime_control.sh start"
echo
echo "Treasury status:"
echo "  bash ~/companyos/scripts/companyos_treasury.sh status"
