#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase18001_19000_$STAMP"

echo "======================================================"
echo " CompanyOS Phase 18001-19000"
echo " CYCLE CLOSURE + POLICY-AWARE RESOLUTION"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"

for f in   "$ROOT/companyos/ceointelligence/verification_engine.py"   "$ROOT/companyos/ceointelligence/ceo_orchestrator.py"
do
  [ -f "$f" ] && cp "$f" "$BACKUP/"
done

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh 2>/dev/null || true
chmod +x "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python "$ROOT/scripts/patch_ceo_cycle_verifier_19000.py"
python "$ROOT/scripts/patch_ceo_orchestrator_19000.py"

python -m py_compile   "$ROOT/companyos/ceointelligence/verification_engine.py"   "$ROOT/companyos/ceointelligence/ceo_orchestrator.py"

python "$ROOT/scripts/phase18001_19000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase18001_19000.py" --disable-warnings

echo
echo "PHASE18001_19000_INSTALL_OK"
echo "OUTCOME_CLASSIFIER=READY"
echo "APPROVAL_DEFERMENT=READY"
echo "DEDUPLICATION_RESOLUTION=READY"
echo "CYCLE_VERIFIER=READY"
echo "ZERO_UNRESOLVED_POLICY=READY"
echo "APPROVAL_BOUNDARIES=PRESERVED"
echo "Backup: $BACKUP"
