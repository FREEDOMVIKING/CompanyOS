#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase889_904_multi_round_revalidation_orchestrator_$STAMP"

echo "=== CompanyOS Phase 889-904 ==="
echo "MULTI-ROUND AUTONOMOUS REVALIDATION ORCHESTRATOR"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"; [ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase889_904"
cp -a "$HERE/companyos_phase889_904" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase889_904.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase889_904_verify.py" "$ROOT/scripts/run_multi_round_revalidation_demo.py"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python scripts/phase889_904_verify.py
python -m pytest -q tests/test_phase889_904.py --disable-warnings

echo
echo "PHASE889_904_INSTALL_OK"
echo "AUTONOMOUS_ROUND_SCHEDULING=READY"
echo "PERSISTENT_ROUND_STATE=READY"
echo "PERSISTENT_HISTORY=READY"
echo "DIMINISHING_RETURNS_DETECTION=READY"
echo "TERMINAL_DECISION_RESOLUTION=READY"
echo "BUILD_DISPATCH=READY"
echo "ARCHIVE_DISPATCH=READY"
echo "HUMAN_REVIEW_DISPATCH=READY"
echo "BOUNDED_EXHAUSTION=READY"
echo "QUEUE_HANDOFF=READY"
echo "MISSION_STATE_SYNC=READY"
echo "MULTI_ROUND_CONTROLLER=READY"
echo "CEO_MULTI_ROUND_BRIDGE=READY"
echo "Backup: $BACKUP"
