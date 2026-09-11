#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase545_560_continuous_ceo_service_watchdog_$STAMP"

echo "=== CompanyOS Phase 545-560 ==="
echo "CONTINUOUS CEO SERVICE + WATCHDOG"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase545_560"
cp -a "$HERE/companyos_phase545_560" "$TARGET/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/test_phase545_560.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_ceo_service.py"
chmod +x "$ROOT/scripts/ceo_service_health.py"
chmod +x "$ROOT/scripts/phase545_560_verify.py"
chmod +x "$ROOT/scripts/start_ceo_service.sh"
chmod +x "$ROOT/scripts/stop_ceo_service.sh"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase545_560_verify.py
python -m pytest -q tests/test_phase545_560.py --disable-warnings

cat > "$ROOT/PHASE545_560_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase545_560_continuous_ceo_service_watchdog","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE545_560_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "CONTINUOUS_CEO_SERVICE=READY"
echo "AUTONOMOUS_SCHEDULER_LOOP=READY"
echo "QUALITY_CYCLE_INTEGRATION=READY"
echo "WATCHDOG=READY"
echo "CRASH_RECOVERY=READY"
echo "SERVICE_LOCK=READY"
echo "SERVICE_JOURNAL=READY"
echo "Backup: $BACKUP"
