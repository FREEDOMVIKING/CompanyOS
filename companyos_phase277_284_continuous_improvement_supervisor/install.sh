#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase277_284_continuous_improvement_supervisor_$STAMP"

echo "=== CompanyOS Phase 277-284 ==="
echo "CONTINUOUS AUTONOMOUS IMPROVEMENT SUPERVISOR"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

[ -d "$TARGET/companyos_phase277_284" ] && cp -a "$TARGET/companyos_phase277_284" "$BACKUP/" || true

rm -rf "$TARGET/companyos_phase277_284"
cp -a "$HERE/companyos_phase277_284" "$TARGET/"
cp "$HERE/scripts/run_continuous_improvement.py" "$ROOT/scripts/"
cp "$HERE/scripts/supervisor_status.py" "$ROOT/scripts/"
cp "$HERE/scripts/phase277_284_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase277_284.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_continuous_improvement.py"
chmod +x "$ROOT/scripts/supervisor_status.py"

cat > "$ROOT/PHASE277_284_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase277_284_continuous_improvement_supervisor","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase277_284_verify.py
python -m pytest -q tests/test_phase277_284.py --disable-warnings

echo
echo "PHASE277_284_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "CONTINUOUS_IMPROVEMENT_SUPERVISOR=READY"
echo "OVERLAP_PROTECTION=TRUE"
echo "FAILURE_LOOP_BREAKER=TRUE"
echo "VERIFICATION_GATES_PRESERVED=TRUE"
echo "Backup: $BACKUP"
