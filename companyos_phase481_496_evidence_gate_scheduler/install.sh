#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase481_496_evidence_gate_scheduler_$STAMP"

echo "=== CompanyOS Phase 481-496 ==="
echo "EVIDENCE GATES + PERSISTENT CEO MISSION SCHEDULER"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase481_496"
cp -a "$HERE/companyos_phase481_496" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase481_496.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/add_validation_metrics.py"
chmod +x "$ROOT/scripts/add_operations_metrics.py"
chmod +x "$ROOT/scripts/run_mission_scheduler.py"
chmod +x "$ROOT/scripts/phase481_496_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase481_496_verify.py
python -m pytest -q tests/test_phase481_496.py --disable-warnings

cat > "$ROOT/PHASE481_496_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase481_496_evidence_gate_scheduler","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE481_496_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "EVIDENCE_GATE_SCHEDULER=READY"
echo "PERSISTENT_MISSION_QUEUE=READY"
echo "VALIDATION_METRICS_STORE=READY"
echo "OPERATIONS_METRICS_STORE=READY"
echo "MISSION_PRIORITY_SCHEDULER=READY"
echo "Backup: $BACKUP"
