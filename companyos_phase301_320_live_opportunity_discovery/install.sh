#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase301_320_live_opportunity_discovery_$STAMP"

echo "=== CompanyOS Phase 301-320 ==="
echo "LIVE OPPORTUNITY DISCOVERY ENGINE"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

[ -d "$TARGET/companyos_phase301_320" ] && cp -a "$TARGET/companyos_phase301_320" "$BACKUP/" || true

rm -rf "$TARGET/companyos_phase301_320"
cp -a "$HERE/companyos_phase301_320" "$TARGET/"
cp "$HERE/scripts/opportunity_discovery_demo.py" "$ROOT/scripts/"
cp "$HERE/scripts/discovery_status.py" "$ROOT/scripts/"
cp "$HERE/scripts/phase301_320_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase301_320.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/opportunity_discovery_demo.py"
chmod +x "$ROOT/scripts/discovery_status.py"

cat > "$ROOT/PHASE301_320_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase301_320_live_opportunity_discovery","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase301_320_verify.py
python -m pytest -q tests/test_phase301_320.py --disable-warnings

echo
echo "PHASE301_320_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "LIVE_OPPORTUNITY_DISCOVERY_ENGINE=READY"
echo "PLUGGABLE_LIVE_SOURCES=TRUE"
echo "PERSISTENT_EVIDENCE_STORE=TRUE"
echo "VALIDATION_QUEUE=TRUE"
echo "CEO_DISCOVERY_LOOP=READY"
echo "Backup: $BACKUP"
