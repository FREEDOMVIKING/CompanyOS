#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase921_936_adaptive_strategy_execution_feedback_$STAMP"

echo "=== CompanyOS Phase 921-936 ==="
echo "ADAPTIVE STRATEGY EXECUTION + VALIDATION FEEDBACK"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"; [ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase921_936"
cp -a "$HERE/companyos_phase921_936" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase921_936.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase921_936_verify.py" "$ROOT/scripts/run_adaptive_strategy_execution_demo.py"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python scripts/phase921_936_verify.py
python -m pytest -q tests/test_phase921_936.py --disable-warnings

echo
echo "PHASE921_936_INSTALL_OK"
echo "ADAPTIVE_PLAN_EXECUTION=READY"
echo "STRATEGY_TASK_DISPATCH=READY"
echo "ADAPTIVE_RESULT_NORMALIZATION=READY"
echo "NOVEL_EVIDENCE_FILTER=READY"
echo "SIGNAL_QUALITY_FILTER=READY"
echo "ADAPTIVE_EVIDENCE_STORE=READY"
echo "VALIDATION_FEEDBACK_BRIDGE=READY"
echo "CONFIDENCE_IMPROVEMENT_GATE=READY"
echo "ADAPTIVE_ROUND_DECISION=READY"
echo "DIMINISHING_RETURN_GUARD=READY"
echo "STRATEGY_EXECUTION_STATE=READY"
echo "STRATEGY_EXECUTION_AUDIT=READY"
echo "ADAPTIVE_CLOSED_LOOP_CONTROLLER=READY"
echo "CEO_ADAPTIVE_EXECUTION_BRIDGE=READY"
echo "Backup: $BACKUP"
