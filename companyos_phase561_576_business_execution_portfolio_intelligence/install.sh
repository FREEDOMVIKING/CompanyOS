#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/phase561_576_business_execution_portfolio_intelligence_$STAMP"

echo "=== CompanyOS Phase 561-576 ==="
echo "BUSINESS EXECUTION + PORTFOLIO INTELLIGENCE"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT missing"; exit 1; }

mkdir -p "$BACKUP" "$ROOT/scripts" "$ROOT/tests"
TARGET="$ROOT"
[ -d "$ROOT/src" ] && TARGET="$ROOT/src"

rm -rf "$TARGET/companyos_phase561_576"
cp -a "$HERE/companyos_phase561_576" "$TARGET/"
cp "$HERE/scripts/"*.py "$ROOT/scripts/"
cp "$HERE/tests/test_phase561_576.py" "$ROOT/tests/"

chmod +x "$ROOT/scripts/run_business_execution_review.py"
chmod +x "$ROOT/scripts/run_portfolio_intelligence.py"
chmod +x "$ROOT/scripts/phase561_576_verify.py"

cd "$ROOT"
if [ "$TARGET" = "$ROOT/src" ]; then
  export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
else
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

python scripts/phase561_576_verify.py
python -m pytest -q tests/test_phase561_576.py --disable-warnings

cat > "$ROOT/PHASE561_576_INSTALLED.json" <<EOF
{"installed":true,"bundle":"phase561_576_business_execution_portfolio_intelligence","installed_at":"$STAMP","backup":"$BACKUP","autonomy_mode":"high"}
EOF

echo
echo "PHASE561_576_INSTALL_OK"
echo "AUTONOMY_MODE=HIGH"
echo "BUSINESS_EXECUTION_MANAGER=READY"
echo "PORTFOLIO_INTELLIGENCE=READY"
echo "STAGE_EVIDENCE_GATES=READY"
echo "COMMITMENT_GATES=READY"
echo "LAUNCH_READINESS=READY"
echo "KILL_SCALE_POLICY=READY"
echo "MISSION_AUDIT_BRIDGE=READY"
echo "Backup: $BACKUP"
