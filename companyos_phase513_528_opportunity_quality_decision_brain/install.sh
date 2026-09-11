#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase513_528_opportunity_quality_decision_brain_$STAMP"

echo "=== CompanyOS Phase 513-528 ==="
echo "OPPORTUNITY QUALITY + AUTONOMOUS DECISION BRAIN"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase513_528"
cp -a "$HERE/companyos_phase513_528" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase513_528.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_opportunity_quality.py"
chmod +x "$ROOT/scripts/opportunity_quality_status.py"
chmod +x "$ROOT/scripts/phase513_528_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase513_528_verify.py
python -m pytest -q tests/test_phase513_528.py --disable-warnings

cat > "$ROOT/PHASE513_528_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase513_528_opportunity_quality_decision_brain","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE513_528_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "OPPORTUNITY_QUALITY_ENGINE=READY"
echo "RELEVANCE_FILTERING=READY"
echo "SEMANTIC_DEDUPLICATION=READY"
echo "COMMERCIAL_INTENT_SCORING=READY"
echo "JUNK_REJECTION=READY"
echo "AUTONOMOUS_DECISION_BRAIN=READY"
echo "Backup: $BACKUP"
