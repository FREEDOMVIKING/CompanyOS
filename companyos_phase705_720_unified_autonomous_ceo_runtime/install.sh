#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase705_720_unified_autonomous_ceo_runtime_$STAMP"

echo "=== CompanyOS Phase 705-720 ==="
echo "UNIFIED AUTONOMOUS CEO RUNTIME"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase705_720"
cp -a "$HERE/companyos_phase705_720" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase705_720.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_unified_ceo_tick.py"
chmod +x "$ROOT/scripts/unified_runtime_status.py"
chmod +x "$ROOT/scripts/phase705_720_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase705_720_verify.py
python -m pytest -q tests/test_phase705_720.py --disable-warnings

cat > "$ROOT/PHASE705_720_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase705_720_unified_autonomous_ceo_runtime","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high_with_governance"}
EOF

echo
echo "PHASE705_720_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH_WITH_GOVERNANCE"
echo "UNIFIED_AUTONOMOUS_CEO_RUNTIME=READY"
echo "SYSTEM_REGISTRY=READY"
echo "CONTEXT_BUS=READY"
echo "GOVERNED_ACTION_ROUTER=READY"
echo "MISSION_EXECUTION_WRAPPER=READY"
echo "OUTCOME_BRIDGE=READY"
echo "LIFECYCLE_FEEDBACK=READY"
echo "STRATEGIC_LEARNING_FEEDBACK=READY"
echo "PORTFOLIO_FEEDBACK=READY"
echo "INTEGRATION_AUDIT=READY"
echo "RUNTIME_HEALTH=READY"
echo "SAFE_MODE_SUPERVISION=READY"
echo "Backup: $BACKUP"
