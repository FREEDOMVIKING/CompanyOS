#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase793_808_live_research_execution_validation_handoff_$STAMP"

echo "=== CompanyOS Phase 793-808 ==="
echo "LIVE MULTI-PROVIDER RESEARCH EXECUTION + VALIDATION HANDOFF"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

CYCLE_FILE="$TARGET/companyos_phase705_720/closed_loop_cycle.py"
[ -f "$CYCLE_FILE" ] && cp "$CYCLE_FILE" "$BACKUP/closed_loop_cycle.py.before"

rm -rf "$TARGET/companyos_phase793_808"
cp -a "$HERE/companyos_phase793_808" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase793_808.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/patch_unified_closed_loop_live_research.py"
chmod +x "$ROOT/scripts/run_live_research_demo.py"
chmod +x "$ROOT/scripts/phase793_808_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase793_808_verify.py
python -m pytest -q tests/test_phase793_808.py --disable-warnings

python scripts/patch_unified_closed_loop_live_research.py
python -m py_compile "$CYCLE_FILE"

echo
echo "PHASE793_808_INSTALL_OK"
echo "LIVE_MULTI_PROVIDER_EXECUTION=READY"
echo "QUALITY_HANDOFF_GATE=READY"
echo "VALIDATION_HANDOFF=READY"
echo "DEFERRED_RESEARCH_POLICY=READY"
echo "PROVIDER_CHAIN_STATE=READY"
echo "RESEARCH_EXECUTION_AUDIT=READY"
echo "CLOSED_LOOP_INTEGRATION=READY"
echo "VALIDATION_QUEUE_BRIDGE=READY"
echo "UNIFIED_CLOSED_LOOP_PATCH=APPLIED"
echo "Backup: $BACKUP"
