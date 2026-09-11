#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase721_736_end_to_end_mission_integration_harness_$STAMP"

echo "=== CompanyOS Phase 721-736 ==="
echo "END-TO-END AUTONOMOUS MISSION INTEGRATION + STRESS HARNESS"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase721_736"
cp -a "$HERE/companyos_phase721_736" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase721_736.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_end_to_end_harness.py"
chmod +x "$ROOT/scripts/run_bounded_stress.py"
chmod +x "$ROOT/scripts/phase721_736_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase721_736_verify.py
python -m pytest -q tests/test_phase721_736.py --disable-warnings

cat > "$ROOT/PHASE721_736_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase721_736_end_to_end_mission_integration_harness","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high_with_governance"}
EOF

echo
echo "PHASE721_736_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH_WITH_GOVERNANCE"
echo "END_TO_END_MISSION_HARNESS=READY"
echo "CONTROLLED_TEST_MISSIONS=READY"
echo "QUEUE_INJECTION=READY"
echo "LIFECYCLE_PROBES=READY"
echo "LEARNING_PROBES=READY"
echo "AUDIT_PROBES=READY"
echo "INTEGRATION_ASSERTIONS=READY"
echo "RECOVERY_PROBES=READY"
echo "BOUNDED_STRESS_TESTING=READY"
echo "Backup: $BACKUP"
