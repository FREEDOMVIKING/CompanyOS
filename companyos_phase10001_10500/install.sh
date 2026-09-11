#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase10001_10500_self_improve_$STAMP"

echo "=== CompanyOS Phase 10001-10500 ==="
echo "SELF-IMPROVING AUTONOMOUS ENTERPRISE"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase10001_10500_verify.py"
chmod +x "$ROOT/scripts/run_phase10500_self_improvement_demo.py"
chmod +x "$ROOT/scripts/companyos_self_improve.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase10001_10500_verify.py
python -m pytest -q tests/test_phase10001_10500.py --disable-warnings

echo
echo "PHASE10001_10500_INSTALL_OK"
echo "PERFORMANCE_BASELINE=READY"
echo "BOTTLENECK_DETECTOR=READY"
echo "IMPROVEMENT_PLANNER=READY"
echo "SAFE_PATCH_GENERATOR=READY"
echo "SANDBOX_VALIDATOR=READY"
echo "REGRESSION_GUARD=READY"
echo "CANARY_CONTROLLER=READY"
echo "LEARNING_POLICY=READY"
echo "KNOWLEDGE_DISTILLER=READY"
echo "STRATEGY_EVOLVER=READY"
echo "ARCHITECTURE_REVIEW=READY"
echo "SELF_IMPROVEMENT_BOUNDARY=READY"
echo "PERSISTENT_SELF_IMPROVEMENT_STATE=READY"
echo "SELF_IMPROVEMENT_AUDIT=READY"
echo "CEO_SELF_IMPROVEMENT_CONTROLLER=READY"
echo "Backup: $BACKUP"
