#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase245_252_live_provider_bridge_$STAMP"

echo "=== CompanyOS Phase 245-252 ==="
echo "LIVE PROVIDER BRIDGE + ACTIVATION"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

[ -d "$TARGET/companyos_phase245_252" ] && cp -a "$TARGET/companyos_phase245_252" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase245_252"
cp -a "$HERE/companyos_phase245_252" "$TARGET/"
cp "$HERE/scripts/companyos_http_coder_adapter.py" "$ROOT/scripts/"
cp "$HERE/scripts/configure_live_provider.sh" "$ROOT/scripts/"
cp "$HERE/scripts/phase245_252_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase245_252.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/companyos_http_coder_adapter.py"
chmod +x "$ROOT/scripts/configure_live_provider.sh"

cat > "$ROOT/PHASE245_252_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase245_252_live_provider_bridge","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase245_252_verify.py

if python -c "import pytest" >/dev/null 2>&1; then
  python -m pytest -q tests/test_phase245_252.py --disable-warnings
fi

echo
echo "PHASE245_252_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "LIVE_PROVIDER_BRIDGE=READY"

if [ -n "${COMPANYOS_PROVIDER_ENDPOINT:-}" ] && [ -n "${COMPANYOS_PROVIDER_MODEL:-}" ]; then
  echo "LIVE_PROVIDER_ENV=PARTIALLY_CONFIGURED"
else
  echo "LIVE_PROVIDER_ENV=NOT_CONFIGURED"
fi

echo "Backup: $BACKUP"
