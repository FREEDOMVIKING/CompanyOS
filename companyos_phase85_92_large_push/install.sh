#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}";HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)";BACKUP="$ROOT/backups/phase85_92_large_push_$STAMP"
echo "=== CompanyOS Phase 85-92 Large Push ==="
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing";exit 1; }
[ -f "$ROOT/PHASE77_84_INSTALLED.json" ] || echo "WARNING: Phase77-84 marker missing; continuing additive install."
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests" "$ROOT/state"
TARGET="$ROOT";[ -d "$ROOT/src" ] && TARGET="$ROOT/src"
[ -d "$TARGET/companyos_phase85_92" ] && cp -a "$TARGET/companyos_phase85_92" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase85_92";cp -a "$HERE/companyos_phase85_92" "$TARGET/"
cp "$HERE/scripts/phase85_92_verify.py" "$ROOT/scripts/";cp "$HERE/tests/test_phase85_92.py" "$ROOT/tests/"
cat > "$ROOT/PHASE85_92_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase85_92_large_push","installed_at":"$STAMP","backup":"$BACKUP","core_overwritten":false}
EOF
cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ];then export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}";else export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}";fi
python scripts/phase85_92_verify.py
echo;echo "PHASE85_92_INSTALL_OK";echo "Backup: $BACKUP"
