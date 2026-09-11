#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase417_432_autonomous_build_bridge_$STAMP"

echo "=== CompanyOS Phase 417-432 ==="
echo "AUTONOMOUS BUILD BRIDGE"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase417_432"
cp -a "$HERE/companyos_phase417_432" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase417_432.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_venture_to_build_demo.py"
chmod +x "$ROOT/scripts/phase417_432_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase417_432_verify.py
python -m pytest -q tests/test_phase417_432.py --disable-warnings

cat > "$ROOT/PHASE417_432_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase417_432_autonomous_build_bridge","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE417_432_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "VENTURE_FACTORY_CONNECTED=TRUE"
echo "SPECIALIST_DISPATCH=READY"
echo "BOUNDED_BUILD_CYCLES=READY"
echo "TEST_REPAIR_LOOP=READY"
echo "RELEASE_CANDIDATE_GATE=READY"
echo "KPI_FEEDBACK_LOOP=READY"
echo "Backup: $BACKUP"
