#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}";HERE="$(cd "$(dirname "$0")" && pwd)";STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase189_196_large_push_$STAMP"
echo "=== CompanyOS Phase 189-196 Large Push ==="
echo "Persistent company kernel + experiment/learning flywheel"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing";exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests";TARGET="$ROOT";[ -d "$ROOT/src" ] && TARGET="$ROOT/src"
[ -d "$TARGET/companyos_phase189_196" ] && cp -a "$TARGET/companyos_phase189_196" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase189_196";cp -a "$HERE/companyos_phase189_196" "$TARGET/"
cp "$HERE/scripts/phase189_196_verify.py" "$ROOT/scripts/";cp "$HERE/tests/test_phase189_196.py" "$ROOT/tests/"
cat > "$ROOT/PHASE189_196_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase189_196_large_push","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF
cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ];then export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}";else export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}";fi
python scripts/phase189_196_verify.py
if python -c "import pytest" >/dev/null 2>&1;then python -m pytest -q tests/test_phase189_196.py --disable-warnings;fi
echo;echo "PHASE189_196_INSTALL_OK";echo "AUTONOMY_MODE=HIGH";echo "PERSISTENT_KERNEL=TRUE";echo "Backup: $BACKUP"
