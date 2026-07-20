#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase141_148_large_push_$STAMP"

echo "=== CompanyOS Phase 141-148 Large Push ==="
echo "Self-directed enterprise expansion"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
[ -f "$ROOT/PHASE133_140_INSTALLED.json" ] || echo "WARNING: Phase133-140 marker missing; continuing additive install."

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

if [ -d "$TARGET/companyos_phase141_148" ]; then
  cp -a "$TARGET/companyos_phase141_148" "$BACKUP/" || true
fi

rm -rf "$TARGET/companyos_phase141_148"
cp -a "$HERE/companyos_phase141_148" "$TARGET/"
cp "$HERE/scripts/phase141_148_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase141_148.py" "$ROOT/tests/"

cat > "$ROOT/PHASE141_148_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase141_148_large_push","installed_at":"$STAMP","backup":"$BACKUP","core_overwritten":false,"autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase141_148_verify.py

if python -c "import pytest" >/dev/null 2>&1; then
  python -m pytest -q tests/test_phase141_148.py --disable-warnings
fi

echo
echo "PHASE141_148_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "Backup: $BACKUP"
