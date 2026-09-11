#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase16501_17000_$STAMP"

echo "================================================"
echo " CompanyOS Phase 16501-17000"
echo " AUTONOMOUS CEO + LIVE INTELLIGENCE INTEGRATION"
echo "================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT does not exist"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"

# Back up files this package replaces.
for f in \
  "$ROOT/scripts/companyos_reasoning_gateway.py" \
  "$ROOT/scripts/companyos_reasoning_control.sh" \
  "$ROOT/scripts/companyos_ceo.py" \
  "$ROOT/scripts/companyos_ceo.sh"
do
  if [ -f "$f" ]; then
    cp "$f" "$BACKUP/"
  fi
done

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/companyos_reasoning_gateway.py"
chmod +x "$ROOT/scripts/companyos_reasoning_control.sh"
chmod +x "$ROOT/scripts/companyos_ceo.py"
chmod +x "$ROOT/scripts/companyos_ceo.sh"
chmod +x "$ROOT/scripts/phase16501_17000_verify.py"
chmod +x "$ROOT/scripts/patch_worker_pool_compat.py"

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python "$ROOT/scripts/patch_worker_pool_compat.py"
python -m py_compile \
  "$ROOT/scripts/companyos_reasoning_gateway.py" \
  "$ROOT/scripts/companyos_ceo.py"

python "$ROOT/scripts/phase16501_17000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase16501_17000.py" --disable-warnings

echo
echo "PHASE16501_17000_INSTALL_OK"
echo "LIVE_REASONING_CLIENT=READY"
echo "AUTONOMOUS_PLANNER=READY"
echo "SPECIALIST_DELEGATION=READY"
echo "APPROVAL_CLASSIFICATION=READY"
echo "EXECUTION_VERIFICATION=READY"
echo "PERSISTENT_LEARNING_MEMORY=READY"
echo "WORKER_QUEUE_INTEGRATION=READY"
echo "REASONING_GATEWAY_OPENROUTER_COMPAT=READY"
echo "Backup: $BACKUP"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_reasoning_control.sh start"
echo "  bash ~/companyos/scripts/companyos_reasoning_control.sh test"
echo "  bash ~/companyos/scripts/companyos_ceo.sh run \"Find the highest-value opportunity CompanyOS should research next\""
