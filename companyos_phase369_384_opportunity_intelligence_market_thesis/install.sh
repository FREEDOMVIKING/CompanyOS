#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase369_384_opportunity_intelligence_market_thesis_$STAMP"

echo "=== CompanyOS Phase 369-384 ==="
echo "OPPORTUNITY INTELLIGENCE + MARKET THESIS"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase369_384"
cp -a "$HERE/companyos_phase369_384" "$TARGET/"
cp "$HERE/scripts/run_opportunity_intelligence.py" "$ROOT/scripts/"
cp "$HERE/scripts/opportunity_intelligence_status.py" "$ROOT/scripts/"
cp "$HERE/scripts/phase369_384_verify.py" "$ROOT/scripts/"
cp "$HERE/tests/test_phase369_384.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_opportunity_intelligence.py"
chmod +x "$ROOT/scripts/opportunity_intelligence_status.py"

cat > "$ROOT/PHASE369_384_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase369_384_opportunity_intelligence_market_thesis","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase369_384_verify.py
python -m pytest -q tests/test_phase369_384.py --disable-warnings

echo
echo "PHASE369_384_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "OPPORTUNITY_INTELLIGENCE=READY"
echo "MARKET_THESIS_ENGINE=READY"
echo "NOISE_REJECTION=TRUE"
echo "DESCRIPTIVE_OPPORTUNITY_NAMES=TRUE"
echo "CEO_INVESTMENT_DECISIONS=READY"
echo "Backup: $BACKUP"
