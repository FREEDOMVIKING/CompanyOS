#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}";HERE="$(cd "$(dirname "$0")" && pwd)";STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase173_180_large_push_$STAMP"
echo "=== CompanyOS Phase 173-180 Large Push ==="
echo "World model + decision learning + sovereign internal orchestration"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing";exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests";TARGET="$ROOT";[ -d "$ROOT/src" ] && TARGET="$ROOT/src"
[ -d "$TARGET/companyos_phase173_180" ] && cp -a "$TARGET/companyos_phase173_180" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase173_180";cp -a "$HERE/companyos_phase173_180" "$TARGET/"
cp "$HERE/scripts/phase173_180_verify.py" "$ROOT/scripts/";cp "$HERE/tests/test_phase173_180.py" "$ROOT/tests/"
cat > "$ROOT/PHASE173_180_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase173_180_large_push","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF
cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ];then export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}";else export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}";fi
python scripts/phase173_180_verify.py
if python -c "import pytest" >/dev/null 2>&1;then python -m pytest -q tests/test_phase173_180.py --disable-warnings;fi
echo;echo "PHASE173_180_INSTALL_OK";echo "AUTONOMY_MODE=HIGH";echo "SELF_DIRECTED_ORCHESTRATION=TRUE";echo "Backup: $BACKUP"
