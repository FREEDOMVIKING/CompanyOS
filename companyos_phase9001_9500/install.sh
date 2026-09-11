#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase9001_9500_actiongov_$STAMP"

echo "=== CompanyOS Phase 9001-9500 ==="
echo "AUTONOMOUS EXTERNAL ACTION GOVERNANCE"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase9001_9500_verify.py"
chmod +x "$ROOT/scripts/run_phase9500_action_governance_demo.py"
chmod +x "$ROOT/scripts/companyos_action_governance.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase9001_9500_verify.py
python -m pytest -q tests/test_phase9001_9500.py --disable-warnings

echo
echo "PHASE9001_9500_INSTALL_OK"
echo "ACTION_POLICY_ENGINE=READY"
echo "PERSISTENT_APPROVAL_QUEUE=READY"
echo "ACTION_RISK_SCORING=READY"
echo "BUDGET_ENFORCEMENT=READY"
echo "ACTION_RATE_LIMITING=READY"
echo "DUAL_CONTROL_POLICY=READY"
echo "DRY_RUN_ENGINE=READY"
echo "CHANGE_SET_BUILDER=READY"
echo "POST_ACTION_VERIFIER=READY"
echo "ROLLBACK_EXECUTOR=READY"
echo "HUMAN_OVERRIDE_REGISTRY=READY"
echo "PERSISTENT_ACTION_GOVERNANCE_STATE=READY"
echo "ACTION_GOVERNANCE_AUDIT=READY"
echo "CEO_ACTION_GOVERNANCE_CONTROLLER=READY"
echo "Backup: $BACKUP"
