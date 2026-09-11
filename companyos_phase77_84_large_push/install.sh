#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"; HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"; BACKUP="$ROOT/backups/phase77_84_large_push_$STAMP"
echo "=== CompanyOS Phase 77-84 Large Push ==="
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
[ -f "$ROOT/PHASE69_76_INSTALLED.json" ] || echo "WARNING: Phase69-76 marker missing; continuing additive install."
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"; [ -d "$ROOT/src" ] && TARGET="$ROOT/src"
[ -d "$TARGET/companyos_phase77_84" ] && cp -a "$TARGET/companyos_phase77_84" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase77_84"; cp -a "$HERE/companyos_phase77_84" "$TARGET/"
cp "$HERE/scripts/phase77_84_verify.py" "$ROOT/scripts/"; cp "$HERE/tests/test_phase77_84.py" "$ROOT/tests/"
cat > "$ROOT/PHASE77_84_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase77_84_large_push","installed_at":"$STAMP","backup":"$BACKUP","core_overwritten":false}
EOF
cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"; else export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"; fi
python scripts/phase77_84_verify.py
echo; echo "PHASE77_84_INSTALL_OK"; echo "Backup: $BACKUP"
