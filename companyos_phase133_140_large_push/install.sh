#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase133_140_large_push_$STAMP"

echo "=== CompanyOS Phase 133-140 Large Push ==="
echo "Autonomous opportunity -> venture -> build -> optimize engine"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
[ -f "$ROOT/PHASE125_132_INSTALLED.json" ] || echo "WARNING: Phase125-132 marker missing; continuing additive install."

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

if [ -d "$TARGET/companyos_phase133_140" ]; then
  cp -a "$TARGET/companyos_phase133_140" "$BACKUP/" || true
fi

rm -rf "$TARGET/companyos_phase133_140"
cp -a "$HERE/companyos_phase133_140" "$TARGET/"
cp "$HERE/scripts/phase133_140_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase133_140.py" "$ROOT/tests/"

cat > "$ROOT/PHASE133_140_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase133_140_large_push","installed_at":"$STAMP","backup":"$BACKUP","core_overwritten":false,"autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase133_140_verify.py

if python -c "import pytest" >/dev/null 2>&1; then
  python -m pytest -q tests/test_phase133_140.py --disable-warnings
fi

echo
echo "PHASE133_140_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "Backup: $BACKUP"
