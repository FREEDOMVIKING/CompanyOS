#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase253_260_live_intelligence_builder_$STAMP"

echo "=== CompanyOS Phase 253-260 ==="
echo "LIVE OPENROUTER INTELLIGENCE -> AUTONOMOUS BUILDER"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

[ -d "$TARGET/companyos_phase253_260" ] && cp -a "$TARGET/companyos_phase253_260" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase253_260"
cp -a "$HERE/companyos_phase253_260" "$TARGET/"

cp "$HERE/scripts/companyos_openrouter_coder.py" "$ROOT/scripts/"
cp "$HERE/scripts/activate_live_intelligence.sh" "$ROOT/scripts/"
cp "$HERE/scripts/live_intelligence_status.py" "$ROOT/scripts/"
cp "$HERE/scripts/phase253_260_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase253_260.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/companyos_openrouter_coder.py"
chmod +x "$ROOT/scripts/activate_live_intelligence.sh"
chmod +x "$ROOT/scripts/live_intelligence_status.py"

cat > "$ROOT/PHASE253_260_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase253_260_live_intelligence_builder","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high","openrouter_builder_bridge":true}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase253_260_verify.py

if python -c "import pytest" >/dev/null 2>&1; then
  python -m pytest -q tests/test_phase253_260.py --disable-warnings
fi

echo
echo "PHASE253_260_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "LIVE_INTELLIGENCE_BUILDER_BRIDGE=READY"

if [ -n "${OPENROUTER_API_KEY:-}" ]; then
  echo "OPENROUTER_KEY=FOUND"
  bash "$ROOT/scripts/activate_live_intelligence.sh" "$ROOT"
else
  echo "OPENROUTER_KEY=NOT_LOADED"
fi

echo "NO_PAID_GENERATION_SENT_DURING_INSTALL=TRUE"
echo "Backup: $BACKUP"
