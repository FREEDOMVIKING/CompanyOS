#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase93_100_large_push_$STAMP"

echo "=== CompanyOS Phase 93-100 Large Push ==="
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

if [ ! -f "$ROOT/PHASE85_92_INSTALLED.json" ]; then
  echo "WARNING: PHASE85_92_INSTALLED.json missing; continuing additive install."
fi

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

if [ -d "$TARGET/companyos_phase93_100" ]; then
  cp -a "$TARGET/companyos_phase93_100" "$BACKUP/" || true
fi

rm -rf "$TARGET/companyos_phase93_100"
cp -a "$HERE/companyos_phase93_100" "$TARGET/"
cp "$HERE/scripts/phase93_100_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase93_100.py" "$ROOT/tests/"

cat > "$ROOT/PHASE93_100_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase93_100_large_push","installed_at":"$STAMP","backup":"$BACKUP","core_overwritten":false}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase93_100_verify.py

echo
echo "PHASE93_100_INSTALL_OK"
echo "Backup: $BACKUP"
