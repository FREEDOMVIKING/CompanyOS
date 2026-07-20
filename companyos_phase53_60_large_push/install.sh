#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase53_60_large_push_$STAMP"

echo "=== CompanyOS Phase 53-60 Large Push ==="
echo "Root: $ROOT"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/state" "$ROOT/scripts" "$ROOT/tests"

# Detect import root without overwriting existing CompanyOS core.
TARGET="$ROOT"
if [ -d "$ROOT/src" ]; then
  TARGET="$ROOT/src"
fi

if [ -d "$TARGET/companyos_phase53_60" ]; then
  cp -a "$TARGET/companyos_phase53_60" "$BACKUP/"
fi

rm -rf "$TARGET/companyos_phase53_60"
cp -a "$HERE/companyos_phase53_60" "$TARGET/companyos_phase53_60"
cp "$HERE/scripts/phase53_60_verify.py" "$ROOT/scripts/phase53_60_verify.py"
cp "$HERE/tests/test_phase53_60.py" "$ROOT/tests/test_phase53_60.py"

cat > "$ROOT/PHASE53_60_INSTALLED.json" <<EOF
{
  "installed": true,
  "bundle": "phase53_60_large_push",
  "installed_at": "$STAMP",
  "target": "$TARGET",
  "backup": "$BACKUP",
  "core_overwritten": false
}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase53_60_verify.py

echo
echo "PHASE53_60_INSTALL_OK"
echo "Backup: $BACKUP"
