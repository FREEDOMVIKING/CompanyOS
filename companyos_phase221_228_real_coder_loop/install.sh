#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase221_228_real_coder_loop_$STAMP"

echo "=== CompanyOS Phase 221-228 ==="
echo "REAL CODER LOOP + AUTONOMOUS REPAIR/REGRESSION"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
[ -f "$ROOT/PHASE205_212_INSTALLED.json" ] || { echo "ERROR: Phase205-212 required"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

[ -d "$TARGET/companyos_phase221_228" ] && cp -a "$TARGET/companyos_phase221_228" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase221_228"
cp -a "$HERE/companyos_phase221_228" "$TARGET/"
cp "$HERE/scripts/phase221_228_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase221_228.py" "$ROOT/tests/"

cat > "$ROOT/PHASE221_228_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase221_228_real_coder_loop","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase221_228_verify.py

if python -c "import pytest" >/dev/null 2>&1; then
  python -m pytest -q tests/test_phase221_228.py --disable-warnings
fi

echo
echo "PHASE221_228_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "REAL_CODER_LOOP_READY=TRUE"

if [ -n "${COMPANYOS_CODER_CMD:-}" ]; then
  echo "EXTERNAL_CODER_ADAPTER=CONFIGURED"
else
  echo "EXTERNAL_CODER_ADAPTER=NOT_CONFIGURED"
  echo "NEXT: configure COMPANYOS_CODER_CMD to activate genuine model-written self-building."
fi

echo "Backup: $BACKUP"
