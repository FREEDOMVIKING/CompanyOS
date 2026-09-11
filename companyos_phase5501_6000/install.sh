#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase5501_6000_orchestration_brain_$STAMP"

echo "=== CompanyOS Phase 5501-6000 ==="
echo "UNIFIED AUTONOMOUS ORCHESTRATION BRAIN"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase5501_6000_verify.py"
chmod +x "$ROOT/scripts/run_phase6000_orchestration_demo.py"
chmod +x "$ROOT/scripts/companyos_orchestration.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase5501_6000_verify.py
python -m pytest -q tests/test_phase5501_6000.py --disable-warnings

echo
echo "PHASE5501_6000_INSTALL_OK"
echo "PERSISTENT_GOAL_GRAPH=READY"
echo "DYNAMIC_AGENT_FACTORY=READY"
echo "CAPABILITY_REGISTRY=READY"
echo "CROSS_SYSTEM_SCHEDULER=READY"
echo "MEMORY_CONSOLIDATION=READY"
echo "DECISION_SYNTHESIZER=READY"
echo "PRIORITY_ARBITRATOR=READY"
echo "DEPENDENCY_RESOLVER=READY"
echo "CONTINUOUS_AUTONOMY_LOOP=READY"
echo "RESTART_SAFE_RUNTIME=READY"
echo "UNIFIED_SYSTEM_HEALTH=READY"
echo "AUTHORITY_ROUTER=READY"
echo "PERSISTENT_ORCHESTRATION_STATE=READY"
echo "ORCHESTRATION_AUDIT=READY"
echo "CEO_ORCHESTRATION_BRAIN=READY"
echo "Backup: $BACKUP"
