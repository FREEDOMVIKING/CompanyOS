#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase449_464_business_operations_growth_loop_$STAMP"

echo "=== CompanyOS Phase 449-464 ==="
echo "BUSINESS OPERATIONS + GROWTH LOOP"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase449_464"
cp -a "$HERE/companyos_phase449_464" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase449_464.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_business_ops_demo.py"
chmod +x "$ROOT/scripts/phase449_464_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase449_464_verify.py
python -m pytest -q tests/test_phase449_464.py --disable-warnings

cat > "$ROOT/PHASE449_464_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase449_464_business_operations_growth_loop","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE449_464_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "BUSINESS_OPERATIONS_GROWTH_LOOP=READY"
echo "LAUNCH_READINESS_GATE=READY"
echo "CUSTOMER_FEEDBACK_LOOP=READY"
echo "SUPPORT_TRIAGE=READY"
echo "GROWTH_EXPERIMENTS=READY"
echo "UNIT_ECONOMICS=READY"
echo "SCALE_ITERATE_PIVOT_DECISIONS=READY"
echo "Backup: $BACKUP"
