#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase641_656_autonomous_operations_customer_success_$STAMP"

echo "=== CompanyOS Phase 641-656 ==="
echo "AUTONOMOUS OPERATIONS + CUSTOMER SUCCESS"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase641_656"
cp -a "$HERE/companyos_phase641_656" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase641_656.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_operations_demo.py"
chmod +x "$ROOT/scripts/phase641_656_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase641_656_verify.py
python -m pytest -q tests/test_phase641_656.py --disable-warnings

cat > "$ROOT/PHASE641_656_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase641_656_autonomous_operations_customer_success","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE641_656_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "AUTONOMOUS_OPERATIONS=READY"
echo "CUSTOMER_SUCCESS=READY"
echo "CUSTOMER_HEALTH=READY"
echo "SUPPORT_TRIAGE=READY"
echo "CHURN_RISK=READY"
echo "RETENTION_ACTIONS=READY"
echo "INCIDENT_MANAGEMENT=READY"
echo "SERVICE_QUALITY=READY"
echo "FEEDBACK_ROUTING=READY"
echo "BOTTLENECK_DETECTION=READY"
echo "OPERATIONS_AUDIT=READY"
echo "Backup: $BACKUP"
