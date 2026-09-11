#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "=============================================="
echo " CompanyOS Phase 19001-20000"
echo " CONTINUOUS AUTONOMY LAYER"
echo "=============================================="

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$ROOT/scripts" "$ROOT/tests"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python -m py_compile   "$ROOT/scripts/companyos_autonomy.py"   "$ROOT/scripts/phase19001_20000_verify.py"

python "$ROOT/scripts/phase19001_20000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase19001_20000.py" --disable-warnings

echo
echo "PHASE19001_20000_INSTALL_OK"
echo "OBJECTIVE_ENGINE=READY"
echo "PRIORITY_ENGINE=READY"
echo "CYCLE_MEMORY=READY"
echo "CONTINUOUS_AUTONOMY_LOOP=READY"
echo "PHASE19000_VERIFIED_CYCLE_INTEGRATION=READY"
echo "EXTERNAL_SIDE_EFFECTS=APPROVAL_GATED"
