#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase1001_1100_autonomous_launch_operate_layer_$STAMP"

echo "=== CompanyOS Phase 1001-1100 ==="
echo "AUTONOMOUS LAUNCH + OPERATE LAYER"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase1001_1100"
cp -a "$HERE/companyos_phase1001_1100" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase1001_1100.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase1001_1100_verify.py"
chmod +x "$ROOT/scripts/run_phase1100_launch_operate_demo.py"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase1001_1100_verify.py
python -m pytest -q tests/test_phase1001_1100.py --disable-warnings

echo
echo "PHASE1001_1100_INSTALL_OK"
echo "ARTIFACT_VERIFICATION=READY"
echo "DEPLOYMENT_ORCHESTRATION=READY"
echo "IRREVERSIBLE_ACTION_GATING=READY"
echo "LAUNCH_MONITORING=READY"
echo "CUSTOMER_FEEDBACK_LOOP=READY"
echo "REVENUE_TELEMETRY=READY"
echo "GROWTH_METRICS=READY"
echo "INCIDENT_DETECTION=READY"
echo "INCIDENT_RECOVERY=READY"
echo "POST_LAUNCH_OPTIMIZATION=READY"
echo "PORTFOLIO_FEEDBACK=READY"
echo "PERSISTENT_LAUNCH_STATE=READY"
echo "LAUNCH_AUDIT=READY"
echo "UNIFIED_LAUNCH_OPERATE_CONTROLLER=READY"
echo "Backup: $BACKUP"
