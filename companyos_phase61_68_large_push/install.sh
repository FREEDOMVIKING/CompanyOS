#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase61_68_large_push_$STAMP"

echo "=== CompanyOS Phase 61-68 Large Push ==="
echo "Root: $ROOT"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }

if [ ! -f "$ROOT/PHASE53_60_INSTALLED.json" ]; then
  echo "WARNING: PHASE53_60_INSTALLED.json not found."
  echo "Continuing because this bundle is additive, but previous phase verification is recommended."
fi

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"

TARGET="$ROOT"
if [ -d "$ROOT/src" ]; then
  TARGET="$ROOT/src"
fi

if [ -d "$TARGET/companyos_phase61_68" ]; then
  cp -a "$TARGET/companyos_phase61_68" "$BACKUP/"
fi

rm -rf "$TARGET/companyos_phase61_68"
cp -a "$HERE/companyos_phase61_68" "$TARGET/companyos_phase61_68"
cp "$HERE/scripts/phase61_68_verify.py" "$ROOT/scripts/phase61_68_verify.py"
cp "$HERE/tests/test_phase61_68.py" "$ROOT/tests/test_phase61_68.py"

cat > "$ROOT/PHASE61_68_INSTALLED.json" <<EOF
{
  "installed": true,
  "bundle": "phase61_68_large_push",
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

python scripts/phase61_68_verify.py

echo
echo "PHASE61_68_INSTALL_OK"
echo "Backup: $BACKUP"
