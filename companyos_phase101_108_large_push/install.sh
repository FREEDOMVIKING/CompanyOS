#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"; HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"; BACKUP="$ROOT/backups/phase101_108_large_push_$STAMP"
echo "=== CompanyOS Phase 101-108 Large Push ==="
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
[ -f "$ROOT/PHASE93_100_INSTALLED.json" ] || echo "WARNING: Phase93-100 marker missing; continuing additive install."
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"; [ -d "$ROOT/src" ] && TARGET="$ROOT/src"
[ -d "$TARGET/companyos_phase101_108" ] && cp -a "$TARGET/companyos_phase101_108" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase101_108"; cp -a "$HERE/companyos_phase101_108" "$TARGET/"
cp "$HERE/scripts/phase101_108_verify.py" "$ROOT/scripts/"; cp "$HERE/tests/test_phase101_108.py" "$ROOT/tests/"
cat > "$ROOT/PHASE101_108_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase101_108_large_push","installed_at":"$STAMP","backup":"$BACKUP","core_overwritten":false}
EOF
cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"; else export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"; fi
python scripts/phase101_108_verify.py
echo; echo "PHASE101_108_INSTALL_OK"; echo "Backup: $BACKUP"
