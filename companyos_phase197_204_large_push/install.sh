#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}";HERE="$(cd "$(dirname "$0")" && pwd)";STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase197_204_large_push_$STAMP"
echo "=== CompanyOS Phase 197-204 Large Push ==="
echo "Always-on CEO + goal continuity + autonomous work generation"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing";exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests";TARGET="$ROOT";[ -d "$ROOT/src" ] && TARGET="$ROOT/src"
[ -d "$TARGET/companyos_phase197_204" ] && cp -a "$TARGET/companyos_phase197_204" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase197_204";cp -a "$HERE/companyos_phase197_204" "$TARGET/"
cp "$HERE/scripts/phase197_204_verify.py" "$ROOT/scripts/";cp "$HERE/tests/test_phase197_204.py" "$ROOT/tests/"
cat > "$ROOT/PHASE197_204_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase197_204_large_push","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF
cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ];then export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}";else export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}";fi
python scripts/phase197_204_verify.py
if python -c "import pytest" >/dev/null 2>&1;then python -m pytest -q tests/test_phase197_204.py --disable-warnings;fi
echo;echo "PHASE197_204_INSTALL_OK";echo "AUTONOMY_MODE=HIGH";echo "ALWAYS_ON_CEO=TRUE";echo "WORK_STARVATION_PREVENTION=TRUE";echo "Backup: $BACKUP"
