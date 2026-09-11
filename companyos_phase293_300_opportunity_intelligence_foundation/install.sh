#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase293_300_opportunity_intelligence_foundation_$STAMP"

echo "=== CompanyOS Phase 293-300 ==="
echo "PERSISTENT LOOP FIX + OPPORTUNITY INTELLIGENCE FOUNDATION"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase293_300"
cp -a "$HERE/companyos_phase293_300" "$TARGET/"
cp "$HERE/scripts/patch_persistent_rounds.py" "$ROOT/scripts/"
cp "$HERE/scripts/opportunity_demo.py" "$ROOT/scripts/"
cp "$HERE/scripts/phase293_300_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase293_300.py" "$ROOT/tests/"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase293_300_verify.py
python -m pytest -q tests/test_phase293_300.py --disable-warnings
python scripts/patch_persistent_rounds.py

cat > "$ROOT/PHASE293_300_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase293_300_opportunity_intelligence_foundation","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE293_300_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "NESTED_CYCLE_FIX=READY"
echo "VISIBLE_PROGRESS=READY"
echo "OPPORTUNITY_INTELLIGENCE_FOUNDATION=READY"
echo "VALIDATION_BEFORE_BUILD=TRUE"
echo "Backup: $BACKUP"
