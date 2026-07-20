#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}";HERE="$(cd "$(dirname "$0")" && pwd)";STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase165_172_large_push_$STAMP"
echo "=== CompanyOS Phase 165-172 Large Push ==="
echo "Persistent company daemon + self-directed initiative lifecycle"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing";exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests";TARGET="$ROOT";[ -d "$ROOT/src" ] && TARGET="$ROOT/src"
[ -d "$TARGET/companyos_phase165_172" ] && cp -a "$TARGET/companyos_phase165_172" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase165_172";cp -a "$HERE/companyos_phase165_172" "$TARGET/"
cp "$HERE/scripts/phase165_172_verify.py" "$ROOT/scripts/";cp "$HERE/tests/test_phase165_172.py" "$ROOT/tests/"
cat > "$ROOT/PHASE165_172_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase165_172_large_push","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF
cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ];then export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}";else export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}";fi
python scripts/phase165_172_verify.py
if python -c "import pytest" >/dev/null 2>&1;then python -m pytest -q tests/test_phase165_172.py --disable-warnings;fi
echo;echo "PHASE165_172_INSTALL_OK";echo "AUTONOMY_MODE=HIGH";echo "PERSISTENT_HEARTBEAT=TRUE";echo "Backup: $BACKUP"
