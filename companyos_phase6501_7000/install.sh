#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase6501_7000_final_validation_$STAMP"
echo "=== CompanyOS Phase 6501-7000 ==="
echo "FINAL INTEGRATION + END-TO-END VALIDATION"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"
chmod +x "$ROOT/scripts/phase6501_7000_verify.py" "$ROOT/scripts/run_phase7000_final_demo.py" "$ROOT/scripts/companyos_final.sh"
cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python scripts/phase6501_7000_verify.py
python -m pytest -q tests/test_phase6501_7000.py --disable-warnings
echo
echo "PHASE6501_7000_INSTALL_OK"
echo "SYSTEM_INVENTORY=READY"
echo "INTEGRATION_VALIDATOR=READY"
echo "END_TO_END_RUNNER=READY"
echo "REGRESSION_MATRIX=READY"
echo "DEPENDENCY_AUDITOR=READY"
echo "CONTINUITY_CHECKER=READY"
echo "RECOVERY_VALIDATOR=READY"
echo "APPROVAL_BOUNDARY_VALIDATOR=READY"
echo "PRODUCTION_READINESS=READY"
echo "SINGLE_COMMAND_RUNTIME=READY"
echo "FINAL_STATE=READY"
echo "FINAL_AUDIT=READY"
echo "FINAL_INTEGRATION_CONTROLLER=READY"
echo "Backup: $BACKUP"
