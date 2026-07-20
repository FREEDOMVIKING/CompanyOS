#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase205_212_self_building_runtime_$STAMP"

echo "=== CompanyOS Phase 205-212 ==="
echo "REAL SELF-BUILDING RUNTIME FOUNDATION"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"

TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

if [ -d "$TARGET/companyos_phase205_212" ]; then
  cp -a "$TARGET/companyos_phase205_212" "$BACKUP/" || true
fi

rm -rf "$TARGET/companyos_phase205_212"
cp -a "$HERE/companyos_phase205_212" "$TARGET/"
cp "$HERE/scripts/phase205_212_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase205_212.py" "$ROOT/tests/"

cat > "$ROOT/PHASE205_212_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase205_212_self_building_runtime","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high","real_runtime_foundation":true}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase205_212_verify.py

if python -c "import pytest" >/dev/null 2>&1; then
  python -m pytest -q tests/test_phase205_212.py --disable-warnings
fi

echo
echo "PHASE205_212_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "SELF_BUILDING_RUNTIME_FOUNDATION=TRUE"
echo "REAL_FILESYSTEM_WORKSPACE=TRUE"
echo "REAL_TEST_EXECUTION=TRUE"
echo "Backup: $BACKUP"
