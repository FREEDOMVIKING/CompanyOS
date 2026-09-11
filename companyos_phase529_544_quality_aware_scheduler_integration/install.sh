#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase529_544_quality_aware_scheduler_integration_$STAMP"

echo "=== CompanyOS Phase 529-544 ==="
echo "QUALITY-AWARE SCHEDULER INTEGRATION"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase529_544"
cp -a "$HERE/companyos_phase529_544" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase529_544.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_quality_scheduler_cycle.py"
chmod +x "$ROOT/scripts/quality_scheduler_status.py"
chmod +x "$ROOT/scripts/phase529_544_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase529_544_verify.py
python -m pytest -q tests/test_phase529_544.py --disable-warnings

cat > "$ROOT/PHASE529_544_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase529_544_quality_aware_scheduler_integration","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE529_544_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "QUALITY_AWARE_SCHEDULER=READY"
echo "QUALITY_MISSION_GENERATION=READY"
echo "CANDIDATE_ROUTING=READY"
echo "TARGETED_RESEARCH_MORE=READY"
echo "VALIDATION_ROUTE=READY"
echo "SCHEDULER_QUALITY_HOOK=READY"
echo "Backup: $BACKUP"
