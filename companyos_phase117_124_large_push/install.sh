#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}";HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)";BACKUP="$ROOT/backups/phase117_124_large_push_$STAMP"
echo "=== CompanyOS Phase 117-124 Large Push ==="
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing";exit 1; }
[ -f "$ROOT/PHASE109_116_INSTALLED.json" ] || echo "WARNING: Phase109-116 marker missing; continuing additive install."
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT";[ -d "$ROOT/src" ] && TARGET="$ROOT/src"
[ -d "$TARGET/companyos_phase117_124" ] && cp -a "$TARGET/companyos_phase117_124" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase117_124";cp -a "$HERE/companyos_phase117_124" "$TARGET/"
cp "$HERE/scripts/phase117_124_verify.py" "$ROOT/scripts/";cp "$HERE/tests/test_phase117_124.py" "$ROOT/tests/"
cat > "$ROOT/PHASE117_124_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase117_124_large_push","installed_at":"$STAMP","backup":"$BACKUP","core_overwritten":false}
EOF
cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ];then export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}";else export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}";fi
python scripts/phase117_124_verify.py
echo;echo "PHASE117_124_INSTALL_OK";echo "Backup: $BACKUP"
