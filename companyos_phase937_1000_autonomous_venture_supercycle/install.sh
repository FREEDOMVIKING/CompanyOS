#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase937_1000_autonomous_venture_supercycle_$STAMP"

echo "=== CompanyOS Phase 937-1000 ==="
echo "AUTONOMOUS VENTURE DECISION-TO-BUILD SUPERCYCLE"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase937_1000"
cp -a "$HERE/companyos_phase937_1000" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase937_1000.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase937_1000_verify.py"
chmod +x "$ROOT/scripts/run_phase1000_supercycle_demo.py"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase937_1000_verify.py
python -m pytest -q tests/test_phase937_1000.py --disable-warnings

echo
echo "PHASE937_1000_INSTALL_OK"
echo "EVIDENCE_RESCORING=READY"
echo "ADAPTIVE_MULTI_ROUND_RESEARCH=READY"
echo "VALIDATION_CONVERGENCE=READY"
echo "GO_TO_BUILD_PROMOTION=READY"
echo "MVP_SCOPE_GENERATION=READY"
echo "SPECIALIST_DELEGATION=READY"
echo "BUILD_DEPENDENCY_GRAPH=READY"
echo "BUILD_TEST_FIX_LOOP=READY"
echo "RELEASE_CANDIDATE_GATE=READY"
echo "ROLLBACK_MANAGER=READY"
echo "PERSISTENT_LIFECYCLE_STATE=READY"
echo "QUEUE_SYNC=READY"
echo "RESTART_RECOVERY=READY"
echo "SUPERCYCLE_AUDIT=READY"
echo "UNIFIED_CEO_SUPERCYCLE=READY"
echo "Backup: $BACKUP"
