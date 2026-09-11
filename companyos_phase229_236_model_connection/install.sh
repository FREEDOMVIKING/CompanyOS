#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase229_236_model_connection_$STAMP"

echo "=== CompanyOS Phase 229-236 ==="
echo "MODEL CONNECTION + AUTONOMOUS HANDOFF LAYER"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
[ -f "$ROOT/PHASE221_228_INSTALLED.json" ] || echo "WARNING: Phase221-228 marker missing; continuing additive install."

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"

TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

[ -d "$TARGET/companyos_phase229_236" ] && cp -a "$TARGET/companyos_phase229_236" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase229_236"
cp -a "$HERE/companyos_phase229_236" "$TARGET/"
cp "$HERE/scripts/companyos_coder_adapter.py" "$ROOT/scripts/"
cp "$HERE/scripts/phase229_236_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase229_236.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/companyos_coder_adapter.py"

cat > "$ROOT/PHASE229_236_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase229_236_model_connection","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase229_236_verify.py

if python -c "import pytest" >/dev/null 2>&1; then
  python -m pytest -q tests/test_phase229_236.py --disable-warnings
fi

echo
echo "PHASE229_236_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "MODEL_CONNECTION_LAYER=READY"

if [ -n "${COMPANYOS_CODER_CMD:-}" ]; then
  echo "EXTERNAL_CODER_ADAPTER=CONFIGURED"
else
  echo "EXTERNAL_CODER_ADAPTER=NOT_CONFIGURED"
fi

echo "Backup: $BACKUP"
