#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase657_672_financial_intelligence_resource_allocation_$STAMP"

echo "=== CompanyOS Phase 657-672 ==="
echo "FINANCIAL INTELLIGENCE + RESOURCE ALLOCATION"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase657_672"
cp -a "$HERE/companyos_phase657_672" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase657_672.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_financial_demo.py"
chmod +x "$ROOT/scripts/phase657_672_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase657_672_verify.py
python -m pytest -q tests/test_phase657_672.py --disable-warnings

cat > "$ROOT/PHASE657_672_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase657_672_financial_intelligence_resource_allocation","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE657_672_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "FINANCIAL_INTELLIGENCE=READY"
echo "BURN_RUNWAY=READY"
echo "PROFITABILITY_ANALYSIS=READY"
echo "ROI_SCORING=READY"
echo "RESOURCE_EFFICIENCY=READY"
echo "PORTFOLIO_CAPITAL_RANKING=READY"
echo "FINANCIAL_ANOMALY_DETECTION=READY"
echo "FORECAST_SCENARIOS=READY"
echo "ALLOCATION_POLICY=READY"
echo "FINANCIAL_AUDIT=READY"
echo "AUTOMATIC_FINANCIAL_TRANSFERS=FALSE"
echo "AUTOMATIC_PURCHASES=FALSE"
echo "Backup: $BACKUP"
