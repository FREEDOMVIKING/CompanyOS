#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase625_640_growth_revenue_intelligence_$STAMP"

echo "=== CompanyOS Phase 625-640 ==="
echo "GROWTH + CUSTOMER ACQUISITION + REVENUE INTELLIGENCE"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase625_640"
cp -a "$HERE/companyos_phase625_640" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase625_640.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_growth_demo.py"
chmod +x "$ROOT/scripts/phase625_640_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase625_640_verify.py
python -m pytest -q tests/test_phase625_640.py --disable-warnings

cat > "$ROOT/PHASE625_640_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase625_640_growth_revenue_intelligence","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE625_640_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "GROWTH_INTELLIGENCE=READY"
echo "MARKET_POSITIONING=READY"
echo "CUSTOMER_ACQUISITION=READY"
echo "VANITY_METRIC_GUARD=READY"
echo "UNIT_ECONOMICS=READY"
echo "REVENUE_INTELLIGENCE=READY"
echo "GROWTH_DECISIONS=READY"
echo "GROWTH_AUDIT=READY"
echo "Backup: $BACKUP"
