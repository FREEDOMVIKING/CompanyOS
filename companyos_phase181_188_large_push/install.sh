#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}";HERE="$(cd "$(dirname "$0")" && pwd)";STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase181_188_large_push_$STAMP"
echo "=== CompanyOS Phase 181-188 Large Push ==="
echo "Enterprise brain + autonomous opportunity incubation"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing";exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests";TARGET="$ROOT";[ -d "$ROOT/src" ] && TARGET="$ROOT/src"
[ -d "$TARGET/companyos_phase181_188" ] && cp -a "$TARGET/companyos_phase181_188" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase181_188";cp -a "$HERE/companyos_phase181_188" "$TARGET/"
cp "$HERE/scripts/phase181_188_verify.py" "$ROOT/scripts/";cp "$HERE/tests/test_phase181_188.py" "$ROOT/tests/"
cat > "$ROOT/PHASE181_188_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase181_188_large_push","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF
cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ];then export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}";else export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}";fi
python scripts/phase181_188_verify.py
if python -c "import pytest" >/dev/null 2>&1;then python -m pytest -q tests/test_phase181_188.py --disable-warnings;fi
echo;echo "PHASE181_188_INSTALL_OK";echo "AUTONOMY_MODE=HIGH";echo "ENTERPRISE_BRAIN_ACTIVE=TRUE";echo "Backup: $BACKUP"
