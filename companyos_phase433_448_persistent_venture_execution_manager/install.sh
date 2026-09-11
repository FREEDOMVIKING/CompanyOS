#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase433_448_persistent_venture_execution_manager_$STAMP"

echo "=== CompanyOS Phase 433-448 ==="
echo "PERSISTENT VENTURE EXECUTION MANAGER"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase433_448"
cp -a "$HERE/companyos_phase433_448" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase433_448.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_portfolio_manager_demo.py"
chmod +x "$ROOT/scripts/phase433_448_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase433_448_verify.py
python -m pytest -q tests/test_phase433_448.py --disable-warnings

cat > "$ROOT/PHASE433_448_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase433_448_persistent_venture_execution_manager","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE433_448_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "PERSISTENT_VENTURE_EXECUTION_MANAGER=READY"
echo "MULTI_VENTURE_QUEUE=READY"
echo "RESOURCE_ALLOCATION=READY"
echo "PRIORITY_ENGINE=READY"
echo "SPECIALIST_COORDINATION=READY"
echo "FAILURE_RETRY_POLICY=READY"
echo "CEO_RESOURCE_ROUTING=READY"
echo "Backup: $BACKUP"
