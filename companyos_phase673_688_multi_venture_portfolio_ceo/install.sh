#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase673_688_multi_venture_portfolio_ceo_$STAMP"

echo "=== CompanyOS Phase 673-688 ==="
echo "MULTI-VENTURE PORTFOLIO CEO + COMPANY CREATION ORCHESTRATION"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase673_688"
cp -a "$HERE/companyos_phase673_688" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase673_688.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_portfolio_ceo_demo.py"
chmod +x "$ROOT/scripts/phase673_688_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase673_688_verify.py
python -m pytest -q tests/test_phase673_688.py --disable-warnings

cat > "$ROOT/PHASE673_688_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase673_688_multi_venture_portfolio_ceo","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE673_688_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "MULTI_VENTURE_PORTFOLIO_CEO=READY"
echo "PORTFOLIO_STRATEGY=READY"
echo "DUPLICATE_AVOIDANCE=READY"
echo "SHARED_RESOURCE_POOL=READY"
echo "KNOWLEDGE_TRANSFER=READY"
echo "INFRASTRUCTURE_REUSE=READY"
echo "PORTFOLIO_PRIORITY=READY"
echo "SUCCESSION_REPLACEMENT_LOGIC=READY"
echo "COMPANY_CREATION_ORCHESTRATION=READY"
echo "PORTFOLIO_AUDIT=READY"
echo "AUTOMATIC_LEGAL_ENTITY_CREATION=FALSE"
echo "AUTOMATIC_EXTERNAL_FINANCIAL_COMMITMENT=FALSE"
echo "Backup: $BACKUP"
