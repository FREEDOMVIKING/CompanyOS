#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"; HERE="$(cd "$(dirname "$0")" && pwd)"; STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase149_156_large_push_$STAMP"
echo "=== CompanyOS Phase 149-156 Large Push ==="
echo "Continuous autonomous CEO evolution"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"; [ -d "$ROOT/src" ] && TARGET="$ROOT/src"
[ -d "$TARGET/companyos_phase149_156" ] && cp -a "$TARGET/companyos_phase149_156" "$BACKUP/" || true
rm -rf "$TARGET/companyos_phase149_156"; cp -a "$HERE/companyos_phase149_156" "$TARGET/"
cp "$HERE/scripts/phase149_156_verify.py" "$ROOT/scripts/"; cp "$HERE/tests/test_phase149_156.py" "$ROOT/tests/"
cat > "$ROOT/PHASE149_156_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase149_156_large_push","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF
cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"; else export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"; fi
python scripts/phase149_156_verify.py
if python -c "import pytest" >/dev/null 2>&1; then python -m pytest -q tests/test_phase149_156.py --disable-warnings; fi
echo; echo "PHASE149_156_INSTALL_OK"; echo "AUTONOMY_MODE=HIGH"; echo "Backup: $BACKUP"
