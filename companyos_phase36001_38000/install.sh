#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 36001-38000"
echo " INTEGRATED AUTONOMOUS RUNTIME"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile   "$ROOT/scripts/companyos_integrated_runtime.py"   "$ROOT/scripts/phase36001_38000_verify.py"

python "$ROOT/scripts/phase36001_38000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase36001_38000.py" --disable-warnings

echo
echo "PHASE36001_38000_INSTALL_OK"
echo "REAL_CAPABILITY_AUTONOMOUS_RUNTIME=READY"
echo "PERSISTENT_CHECKPOINTING=READY"
echo "RUNTIME_HEALTH=READY"
echo "AUTOMATIC_RECOVERY_CLASSIFICATION=READY"
echo "APPROVAL_PAUSE_AND_RESUME=READY"
echo "MISSING_CAPABILITY_DETECTION=READY"
echo "FALSE_COMPLETION_PREVENTION=READY"
echo "LIVE_MONEY_AUTO_ENABLE=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_runtime_integration.sh once"
echo "  bash ~/companyos/scripts/companyos_runtime_integration.sh status"
