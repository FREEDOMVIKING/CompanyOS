#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase321_336_live_research_connectors_$STAMP"

echo "=== CompanyOS Phase 321-336 ==="
echo "LIVE RESEARCH CONNECTORS"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

[ -d "$TARGET/companyos_phase321_336" ] && cp -a "$TARGET/companyos_phase321_336" "$BACKUP/" || true

rm -rf "$TARGET/companyos_phase321_336"
cp -a "$HERE/companyos_phase321_336" "$TARGET/"
cp "$HERE/scripts/configure_research_sources.py" "$ROOT/scripts/"
cp "$HERE/scripts/run_live_research_cycle.py" "$ROOT/scripts/"
cp "$HERE/scripts/research_connector_status.py" "$ROOT/scripts/"
cp "$HERE/scripts/phase321_336_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase321_336.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/configure_research_sources.py"
chmod +x "$ROOT/scripts/run_live_research_cycle.py"
chmod +x "$ROOT/scripts/research_connector_status.py"

cat > "$ROOT/PHASE321_336_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase321_336_live_research_connectors","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase321_336_verify.py
python -m pytest -q tests/test_phase321_336.py --disable-warnings

echo
echo "PHASE321_336_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "LIVE_RESEARCH_CONNECTORS=READY"
echo "RSS_ATOM=TRUE"
echo "JSON_API=TRUE"
echo "TEXT_PAGE=TRUE"
echo "CEO_DISCOVERY_BRIDGE=READY"
echo "Backup: $BACKUP"
