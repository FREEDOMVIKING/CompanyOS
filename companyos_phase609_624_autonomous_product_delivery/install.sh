#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase609_624_autonomous_product_delivery_$STAMP"

echo "=== CompanyOS Phase 609-624 ==="
echo "AUTONOMOUS PRODUCT DELIVERY + OUTCOME ORCHESTRATION"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase609_624"
cp -a "$HERE/companyos_phase609_624" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase609_624.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_product_delivery_demo.py"
chmod +x "$ROOT/scripts/phase609_624_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase609_624_verify.py
python -m pytest -q tests/test_phase609_624.py --disable-warnings

cat > "$ROOT/PHASE609_624_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase609_624_autonomous_product_delivery","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE609_624_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "AUTONOMOUS_PRODUCT_DELIVERY=READY"
echo "PRODUCT_SPEC_ENGINE=READY"
echo "SPECIALIST_DELIVERY_PLAN=READY"
echo "BUILD_ACCEPTANCE_GATE=READY"
echo "QA_GATE=READY"
echo "RELEASE_CANDIDATE_PROMOTION=READY"
echo "DEPLOYMENT_READINESS=READY"
echo "TELEMETRY_CONTRACT=READY"
echo "OUTCOME_FEEDBACK=READY"
echo "Backup: $BACKUP"
