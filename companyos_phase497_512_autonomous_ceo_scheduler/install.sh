#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase497_512_autonomous_ceo_scheduler_$STAMP"

echo "=== CompanyOS Phase 497-512 ==="
echo "AUTONOMOUS CEO MISSION GENERATION + SCHEDULER"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase497_512"
cp -a "$HERE/companyos_phase497_512" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase497_512.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_ceo_scheduler_tick.py"
chmod +x "$ROOT/scripts/ceo_scheduler_status.py"
chmod +x "$ROOT/scripts/phase497_512_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase497_512_verify.py
python -m pytest -q tests/test_phase497_512.py --disable-warnings

cat > "$ROOT/PHASE497_512_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase497_512_autonomous_ceo_scheduler","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE497_512_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "AUTONOMOUS_CEO_SCHEDULER=READY"
echo "MISSION_GENERATION=READY"
echo "DEPENDENCY_RESOLUTION=READY"
echo "EVENT_STREAM=READY"
echo "DYNAMIC_REPRIORITIZATION=READY"
echo "STALLED_WORK_DETECTION=READY"
echo "Backup: $BACKUP"
