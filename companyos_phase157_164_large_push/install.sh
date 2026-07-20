#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"; HERE="$(cd "$(dirname "$0")" && pwd)"; STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase157_164_large_push_$STAMP"
echo "=== CompanyOS Phase 157-164 Large Push ==="
echo "Persistent executive autonomy + mission orchestration"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"; TARGET="$ROOT"; [ -d "$ROOT/src" ] && TARGET="$ROOT/src"
[ -d "$TARGET/companyos_phase157_164" ] && cp -a "$TARGET/companyos_phase157_164" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase157_164"; cp -a "$HERE/companyos_phase157_164" "$TARGET/"
cp "$HERE/scripts/phase157_164_verify.py" "$ROOT/scripts/"; cp "$HERE/tests/test_phase157_164.py" "$ROOT/tests/"
cat > "$ROOT/PHASE157_164_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase157_164_large_push","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF
cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"; else export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"; fi
python scripts/phase157_164_verify.py
if python -c "import pytest" >/dev/null 2>&1; then python -m pytest -q tests/test_phase157_164.py --disable-warnings; fi
echo; echo "PHASE157_164_INSTALL_OK"; echo "AUTONOMY_MODE=HIGH"; echo "CONTINUOUS_OPERATION=TRUE"; echo "Backup: $BACKUP"
