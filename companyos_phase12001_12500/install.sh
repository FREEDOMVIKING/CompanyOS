#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase12001_12500_governance_$STAMP"

echo "=== CompanyOS Phase 12001-12500 ==="
echo "AUTONOMOUS GOVERNANCE + COMPLIANCE COMMAND"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/phase12001_12500_verify.py"
chmod +x "$ROOT/scripts/run_phase12500_governance_demo.py"
chmod +x "$ROOT/scripts/companyos_governance.sh"

cd "$ROOT"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python scripts/phase12001_12500_verify.py
python -m pytest -q tests/test_phase12001_12500.py --disable-warnings

echo
echo "PHASE12001_12500_INSTALL_OK"
echo "POLICY_REGISTRY=READY"
echo "COMPLIANCE_MATRIX=READY"
echo "CONTROL_EVIDENCE_COLLECTOR=READY"
echo "DECISION_LEDGER=READY"
echo "DATA_GOVERNANCE_ENGINE=READY"
echo "RETENTION_POLICY_ENGINE=READY"
echo "ACCESS_REVIEW_ENGINE=READY"
echo "VENDOR_GOVERNANCE_ENGINE=READY"
echo "CONTINUOUS_COMPLIANCE_MONITOR=READY"
echo "AUDIT_READINESS_ENGINE=READY"
echo "POLICY_EXCEPTION_MANAGER=READY"
echo "GOVERNANCE_AUTHORITY_BOUNDARY=READY"
echo "PERSISTENT_GOVERNANCE_STATE=READY"
echo "GOVERNANCE_AUDIT=READY"
echo "CEO_GOVERNANCE_OPS_CONTROLLER=READY"
echo "Backup: $BACKUP"
