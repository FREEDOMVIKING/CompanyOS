#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase577_592_autonomous_venture_lifecycle_feedback_$STAMP"

echo "=== CompanyOS Phase 577-592 ==="
echo "AUTONOMOUS VENTURE LIFECYCLE + OUTCOME FEEDBACK LOOP"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase577_592"
cp -a "$HERE/companyos_phase577_592" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase577_592.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_lifecycle_demo.py"
chmod +x "$ROOT/scripts/phase577_592_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase577_592_verify.py
python -m pytest -q tests/test_phase577_592.py --disable-warnings

cat > "$ROOT/PHASE577_592_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase577_592_autonomous_venture_lifecycle_feedback","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE577_592_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "AUTONOMOUS_VENTURE_LIFECYCLE=READY"
echo "OUTCOME_FEEDBACK_LOOP=READY"
echo "STABLE_VENTURE_IDENTITY=READY"
echo "STAGE_ADVANCEMENT=READY"
echo "NEXT_MISSION_GENERATION=READY"
echo "PROGRESS_GUARD=READY"
echo "PORTFOLIO_FEEDBACK=READY"
echo "LIFECYCLE_AUDIT=READY"
echo "Backup: $BACKUP"
