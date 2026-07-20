#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase125_132_large_push_$STAMP"

echo "=== CompanyOS Phase 125-132 Large Push ==="
echo "Autonomy-first authority model"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

[ -f "$ROOT/PHASE117_124_INSTALLED.json" ] || echo "WARNING: Phase117-124 marker missing; continuing additive install."

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

if [ -d "$TARGET/companyos_phase125_132" ]; then
  cp -a "$TARGET/companyos_phase125_132" "$BACKUP/" || true
fi

rm -rf "$TARGET/companyos_phase125_132"
cp -a "$HERE/companyos_phase125_132" "$TARGET/"
cp "$HERE/scripts/phase125_132_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase125_132.py" "$ROOT/tests/"

cat > "$ROOT/PHASE125_132_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase125_132_large_push","installed_at":"$STAMP","backup":"$BACKUP","core_overwritten":false,"autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase125_132_verify.py

if python -c "import pytest" >/dev/null 2>&1; then
  python -m pytest -q tests/test_phase125_132.py --disable-warnings
fi

echo
echo "PHASE125_132_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "Backup: $BACKUP"
