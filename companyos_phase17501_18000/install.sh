#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase17501_18000_$STAMP"

echo "=============================================="
echo " CompanyOS Phase 17501-18000"
echo " FAILURE CLOSURE + VERIFICATION RELIABILITY"
echo "=============================================="

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"

for f in   "$ROOT/companyos/workerops/execution_bridge.py"   "$ROOT/companyos/ceointelligence/verification_engine.py"
do
  [ -f "$f" ] && cp "$f" "$BACKUP/"
done

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

cp "$HERE/scripts/execution_bridge_phase18000.py"    "$ROOT/companyos/workerops/execution_bridge.py"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python "$ROOT/scripts/patch_ceo_verification_18000.py"

python -m py_compile   "$ROOT/companyos/workerops/execution_bridge.py"   "$ROOT/companyos/ceointelligence/verification_engine.py"

python "$ROOT/scripts/phase17501_18000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase17501_18000.py" --disable-warnings

echo
echo "PHASE17501_18000_INSTALL_OK"
echo "FAILURE_CLASSIFIER=READY"
echo "GENERIC_RECOVERY_SPECIALIST=READY"
echo "RECOVERY_ROUTER=READY"
echo "VERIFICATION_POLICY=READY"
echo "APPROVAL_BOUNDARIES=PRESERVED"
echo "Backup: $BACKUP"
