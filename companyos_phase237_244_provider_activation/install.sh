#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase237_244_provider_activation_$STAMP"

echo "=== CompanyOS Phase 237-244 ==="
echo "PROVIDER ACTIVATION + FIRST REAL SELF-BUILD HANDOFF"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

[ -d "$TARGET/companyos_phase237_244" ] && cp -a "$TARGET/companyos_phase237_244" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase237_244"
cp -a "$HERE/companyos_phase237_244" "$TARGET/"
cp "$HERE/scripts/phase237_244_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase237_244.py" "$ROOT/tests/"

cat > "$ROOT/PHASE237_244_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase237_244_provider_activation","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase237_244_verify.py

if python -c "import pytest" >/dev/null 2>&1; then
  python -m pytest -q tests/test_phase237_244.py --disable-warnings
fi

echo
echo "PHASE237_244_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "PROVIDER_ACTIVATION_LAYER=READY"

if [ -n "${COMPANYOS_CODER_CMD:-}" ] && [ -n "${COMPANYOS_PROVIDER_ADAPTER_CMD:-}" ]; then
  echo "REAL_MODEL_CONNECTION_ENV=CONFIGURED"
else
  echo "REAL_MODEL_CONNECTION_ENV=NOT_CONFIGURED"
fi

echo "Backup: $BACKUP"
