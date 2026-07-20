#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase285_292_persistent_self_improvement_$STAMP"

echo "=== CompanyOS Phase 285-292 ==="
echo "PERSISTENT SELF-IMPROVEMENT RUNTIME"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

[ -d "$TARGET/companyos_phase285_292" ] && cp -a "$TARGET/companyos_phase285_292" "$BACKUP/" || true

rm -rf "$TARGET/companyos_phase285_292"
cp -a "$HERE/companyos_phase285_292" "$TARGET/"
cp "$HERE/scripts/run_persistent_improvement.py" "$ROOT/scripts/"
cp "$HERE/scripts/persistent_control.py" "$ROOT/scripts/"
cp "$HERE/scripts/phase285_292_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase285_292.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_persistent_improvement.py"
chmod +x "$ROOT/scripts/persistent_control.py"

cat > "$ROOT/PHASE285_292_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase285_292_persistent_self_improvement","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase285_292_verify.py
python -m pytest -q tests/test_phase285_292.py --disable-warnings

echo
echo "PHASE285_292_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "PERSISTENT_SELF_IMPROVEMENT=READY"
echo "DURABLE_RESUME_STATE=TRUE"
echo "PAUSE_RESUME_CONTROL=TRUE"
echo "VERIFICATION_GATES_PRESERVED=TRUE"
echo "Backup: $BACKUP"
