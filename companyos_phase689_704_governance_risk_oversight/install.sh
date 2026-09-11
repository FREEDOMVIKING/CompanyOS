#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase689_704_governance_risk_oversight_$STAMP"

echo "=== CompanyOS Phase 689-704 ==="
echo "AUTONOMOUS GOVERNANCE + RISK CONTROLS + EXECUTIVE OVERSIGHT"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase689_704"
cp -a "$HERE/companyos_phase689_704" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase689_704.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_governance_demo.py"
chmod +x "$ROOT/scripts/governance_status.py"
chmod +x "$ROOT/scripts/phase689_704_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase689_704_verify.py
python -m pytest -q tests/test_phase689_704.py --disable-warnings

cat > "$ROOT/PHASE689_704_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase689_704_governance_risk_oversight","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high_with_governance"}
EOF

echo
echo "PHASE689_704_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH_WITH_GOVERNANCE"
echo "AUTHORITY_MATRIX=READY"
echo "RISK_CLASSIFICATION=READY"
echo "APPROVAL_GATEWAY=READY"
echo "FINANCIAL_EXPOSURE_LIMITS=READY"
echo "EXTERNAL_ACTION_CONTROLS=READY"
echo "LEAST_PRIVILEGE_SECRETS=READY"
echo "AGENT_PERMISSION_BOUNDARIES=READY"
echo "PREFLIGHT_CHECKS=READY"
echo "ROLLBACK_REQUIREMENTS=READY"
echo "SAFE_MODE=READY"
echo "POLICY_VIOLATION_DETECTION=READY"
echo "EXECUTIVE_ESCALATION_QUEUE=READY"
echo "DECISION_PROVENANCE=READY"
echo "GOVERNANCE_LEDGER=READY"
echo "Backup: $BACKUP"
