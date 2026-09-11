#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase809_824_queue_recovery_validation_promotion_$STAMP"

echo "=== CompanyOS Phase 809-824 ==="
echo "AUTONOMOUS QUEUE RECOVERY + VALIDATION PROMOTION"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

QUEUE_FILE="$ROOT/.companyos_runtime/ceo_mission_queue.json"
[ -f "$QUEUE_FILE" ] && cp "$QUEUE_FILE" "$BACKUP/ceo_mission_queue.json.before"

rm -rf "$TARGET/companyos_phase809_824"
cp -a "$HERE/companyos_phase809_824" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase809_824.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_queue_recovery.py"
chmod +x "$ROOT/scripts/queue_recovery_status.py"
chmod +x "$ROOT/scripts/phase809_824_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase809_824_verify.py
python -m pytest -q tests/test_phase809_824.py --disable-warnings

echo
echo "PHASE809_824_INSTALL_OK"
echo "DEFERRED_RECOVERY=READY"
echo "RETRY_LOOP_GUARD=READY"
echo "MISSION_DEDUPLICATION=READY"
echo "TEST_MISSION_RETIREMENT=READY"
echo "ALTERNATE_PROVIDER_RECOVERY=READY"
echo "EVIDENCE_MERGE=READY"
echo "VALIDATION_PROMOTION=READY"
echo "QUEUE_COMPACTION=READY"
echo "QUEUE_DRAIN_METRICS=READY"
echo "RECOVERY_AUDIT=READY"
echo "Backup: $BACKUP"
