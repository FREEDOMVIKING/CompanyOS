#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"; HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"; BACKUP="$ROOT/backups/phase69_76_large_push_$STAMP"
echo "=== CompanyOS Phase 69-76 Large Push ==="
[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }
[ -f "$ROOT/PHASE61_68_INSTALLED.json" ] || echo "WARNING: Phase61-68 marker missing."
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"; [ -d "$ROOT/src" ] && TARGET="$ROOT/src"
[ -d "$TARGET/companyos_phase69_76" ] && cp -a "$TARGET/companyos_phase69_76" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase69_76"
cp -a "$HERE/companyos_phase69_76" "$TARGET/"
cp "$HERE/scripts/phase69_76_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase69_76.py" "$ROOT/tests/"
cat > "$ROOT/PHASE69_76_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase69_76_large_push","installed_at":"$STAMP","backup":"$BACKUP","core_overwritten":false}
EOF
cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"; else export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"; fi
python scripts/phase69_76_verify.py
echo
echo "PHASE69_76_INSTALL_OK"
echo "Backup: $BACKUP"
