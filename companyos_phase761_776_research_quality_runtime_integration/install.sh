#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase761_776_research_quality_runtime_integration_$STAMP"

echo "=== CompanyOS Phase 761-776 ==="
echo "RESEARCH QUALITY RUNTIME INTEGRATION"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"; [ -d "$ROOT/src" ] && TARGET="$ROOT/src"
CYCLE_FILE="$TARGET/companyos_phase705_720/closed_loop_cycle.py"
[ -f "$CYCLE_FILE" ] && cp "$CYCLE_FILE" "$BACKUP/closed_loop_cycle.py.before"

rm -rf "$TARGET/companyos_phase761_776"
cp -a "$HERE/companyos_phase761_776" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase761_776.py" "$ROOT/tests/"
chmod +x "$ROOT/scripts/patch_closed_loop_research_quality.py" "$ROOT/scripts/phase761_776_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase761_776_verify.py
python -m pytest -q tests/test_phase761_776.py --disable-warnings
python scripts/patch_closed_loop_research_quality.py
python -m py_compile "$CYCLE_FILE"

echo
echo "PHASE761_776_INSTALL_OK"
echo "RESEARCH_MISSION_ADAPTER=READY"
echo "PROVIDER_HEALTH_BRIDGE=READY"
echo "EVIDENCE_QUALITY_GATE=READY"
echo "RESEARCH_EXECUTION_POLICY=READY"
echo "FALLBACK_CYCLE=READY"
echo "LIFECYCLE_EVIDENCE_BRIDGE=READY"
echo "LEARNING_EVIDENCE_BRIDGE=READY"
echo "RESEARCH_RETRY_STATE=READY"
echo "RESEARCH_AUDIT=READY"
echo "CLOSED_LOOP_RESEARCH_QUALITY_PATCH=APPLIED"
echo "CEO_RESEARCH_RUNTIME_BRIDGE=READY"
echo "Backup: $BACKUP"
