#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase593_608_strategic_learning_adaptive_replanning_$STAMP"

echo "=== CompanyOS Phase 593-608 ==="
echo "STRATEGIC LEARNING + ADAPTIVE MISSION REPLANNING"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase593_608"
cp -a "$HERE/companyos_phase593_608" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase593_608.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_strategic_learning_demo.py"
chmod +x "$ROOT/scripts/phase593_608_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase593_608_verify.py
python -m pytest -q tests/test_phase593_608.py --disable-warnings

cat > "$ROOT/PHASE593_608_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase593_608_strategic_learning_adaptive_replanning","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE593_608_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "STRATEGIC_LEARNING=READY"
echo "HYPOTHESIS_UPDATES=READY"
echo "STRATEGY_ADJUSTMENT=READY"
echo "MISSION_REWRITING=READY"
echo "PORTFOLIO_LEARNING=READY"
echo "LEARNING_AUDIT=READY"
echo "ADAPTIVE_REPLANNER=READY"
echo "Backup: $BACKUP"
