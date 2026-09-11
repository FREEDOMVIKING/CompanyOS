#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase20001_21000_$STAMP"

echo "================================================"
echo " CompanyOS Phase 20001-21000"
echo " AUTONOMOUS RECOVERY + RE-VERIFICATION"
echo "================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"

if [ -f "$ROOT/companyos/ceointelligence/ceo_orchestrator.py" ]; then
  cp "$ROOT/companyos/ceointelligence/ceo_orchestrator.py" "$BACKUP/"
fi

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python "$ROOT/scripts/patch_ceo_recovery_21000.py"

python -m py_compile   "$ROOT/companyos/ceointelligence/ceo_orchestrator.py"   "$ROOT/scripts/phase20001_21000_verify.py"

python "$ROOT/scripts/phase20001_21000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase20001_21000.py" --disable-warnings

echo
echo "PHASE20001_21000_INSTALL_OK"
echo "DIAGNOSTIC_ENGINE=READY"
echo "MISSING_INPUT_RECOVERY=READY"
echo "BOUNDED_RETRY_POLICY=READY"
echo "AUTOMATIC_REVERIFICATION=READY"
echo "APPROVAL_BOUNDARIES=PRESERVED"
echo "Backup: $BACKUP"
