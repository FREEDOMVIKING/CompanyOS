#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"; HERE="$(cd "$(dirname "$0")" && pwd)"; STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase13001_13500_customer_$STAMP"
echo "=== CompanyOS Phase 13001-13500 ==="
echo "AUTONOMOUS CUSTOMER SUCCESS + SERVICE COMMAND"
[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }
mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
cp -r "$HERE/companyos" "$ROOT/"; cp "$HERE/scripts/"* "$ROOT/scripts/"; cp "$HERE/tests/"* "$ROOT/tests/"
chmod +x "$ROOT/scripts/phase13001_13500_verify.py" "$ROOT/scripts/run_phase13500_customer_demo.py" "$ROOT/scripts/companyos_customer.sh"
cd "$ROOT"; export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python scripts/phase13001_13500_verify.py
python -m pytest -q tests/test_phase13001_13500.py --disable-warnings
echo
echo "PHASE13001_13500_INSTALL_OK"
echo "CUSTOMER_HEALTH_ENGINE=READY"
echo "SUPPORT_TRIAGE_ENGINE=READY"
echo "CUSTOMER_SUCCESS_PLANNER=READY"
echo "CHURN_RISK_ENGINE=READY"
echo "RENEWAL_READINESS_ENGINE=READY"
echo "FEEDBACK_INTELLIGENCE_ENGINE=READY"
echo "SLA_ENGINE=READY"
echo "CUSTOMER_KNOWLEDGE_ENGINE=READY"
echo "ESCALATION_ENGINE=READY"
echo "SERVICE_QUALITY_ENGINE=READY"
echo "CUSTOMER_AUTHORITY_BOUNDARY=READY"
echo "PERSISTENT_CUSTOMER_OPS_STATE=READY"
echo "CUSTOMER_OPS_AUDIT=READY"
echo "CEO_CUSTOMER_OPS_CONTROLLER=READY"
echo "Backup: $BACKUP"
