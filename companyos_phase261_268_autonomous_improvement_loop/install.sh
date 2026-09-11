#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase261_268_autonomous_improvement_loop_$STAMP"

echo "=== CompanyOS Phase 261-268 ==="
echo "AUTONOMOUS INTERNAL CAPABILITY-IMPROVEMENT LOOP"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

[ -d "$TARGET/companyos_phase261_268" ] && cp -a "$TARGET/companyos_phase261_268" "$BACKUP/" || true

rm -rf "$TARGET/companyos_phase261_268"
cp -a "$HERE/companyos_phase261_268" "$TARGET/"

cp "$HERE/scripts/run_autonomous_improvement_once.py" "$ROOT/scripts/"
cp "$HERE/scripts/continuous_improvement_status.py" "$ROOT/scripts/"
cp "$HERE/scripts/phase261_268_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase261_268.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_autonomous_improvement_once.py"
chmod +x "$ROOT/scripts/continuous_improvement_status.py"

cat > "$ROOT/PHASE261_268_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase261_268_autonomous_improvement_loop","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase261_268_verify.py
python -m pytest -q tests/test_phase261_268.py --disable-warnings

echo
echo "PHASE261_268_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "AUTONOMOUS_IMPROVEMENT_LOOP=READY"
echo "NO_EXTERNAL_ACTIONS_ADDED_BY_THIS_LOOP=TRUE"
echo "NO_FINANCIAL_ACTIONS_ADDED_BY_THIS_LOOP=TRUE"
echo "Backup: $BACKUP"
