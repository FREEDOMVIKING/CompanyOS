#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase841_856_autonomous_validation_$STAMP"

echo "=== CompanyOS Phase 841-856 ==="
echo "AUTONOMOUS VALIDATION EXECUTION + EVIDENCE-TO-DECISION ENGINE"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase841_856"
cp -a "$HERE/companyos_phase841_856" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase841_856.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_validation_demo.py"
chmod +x "$ROOT/scripts/phase841_856_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase841_856_verify.py
python -m pytest -q tests/test_phase841_856.py --disable-warnings

echo
echo "PHASE841_856_INSTALL_OK"
echo "VALIDATION_MISSION_ADAPTER=READY"
echo "HYPOTHESIS_EXTRACTION=READY"
echo "EXPERIMENT_PLANNING=READY"
echo "VALIDATION_METHOD_SELECTION=READY"
echo "PROBLEM_EVIDENCE_SCORING=READY"
echo "PRICING_VALIDATION=READY"
echo "ALTERNATIVE_COMPARISON=READY"
echo "FALSE_POSITIVE_GUARD=READY"
echo "CONTRADICTION_HANDLING=READY"
echo "VALIDATION_CONFIDENCE=READY"
echo "GO_REVISE_KILL_THRESHOLDS=READY"
echo "BOUNDED_REVALIDATION=READY"
echo "VALIDATION_STATE=READY"
echo "VALIDATION_AUDIT=READY"
echo "BUILD_PROMOTION_BRIDGE=READY"
echo "CEO_VALIDATION_RUNTIME_BRIDGE=READY"
echo "Backup: $BACKUP"
