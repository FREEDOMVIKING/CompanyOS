#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase465_480_persistent_ceo_operating_loop_$STAMP"

echo "=== CompanyOS Phase 465-480 ==="
echo "PERSISTENT CEO OPERATING LOOP"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase465_480"
cp -a "$HERE/companyos_phase465_480" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase465_480.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_persistent_ceo.py"
chmod +x "$ROOT/scripts/ceo_loop_status.py"
chmod +x "$ROOT/scripts/phase465_480_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase465_480_verify.py
python -m pytest -q tests/test_phase465_480.py --disable-warnings

cat > "$ROOT/PHASE465_480_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase465_480_persistent_ceo_operating_loop","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE465_480_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "PERSISTENT_CEO_OPERATING_LOOP=READY"
echo "OPPORTUNITY_STAGE=CONNECTED"
echo "VALIDATION_STAGE=CONNECTED"
echo "VENTURE_STAGE=CONNECTED"
echo "BUILD_STAGE=CONNECTED"
echo "OPERATIONS_STAGE=CONNECTED"
echo "PORTFOLIO_STAGE=CONNECTED"
echo "DECISION_JOURNAL=READY"
echo "Backup: $BACKUP"
