#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${1:-$HOME/companyos}"
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "======================================================"
echo " CompanyOS Phase 54001-65000"
echo " FINAL BOUNDED LIVE FINANCIAL INTEGRATION"
echo "======================================================"

[ -d "$ROOT" ] || { echo "ERROR: $ROOT not found"; exit 1; }
[ -f "$ROOT/agents/multichain_execution_adapter.py" ] || {
  echo "ERROR: multichain execution adapter missing"
  exit 1
}

mkdir -p "$ROOT/scripts" "$ROOT/tests" "$ROOT/.companyos_runtime"

cp -r "$HERE/companyos" "$ROOT/"
cp "$HERE/scripts/"* "$ROOT/scripts/"
cp "$HERE/tests/"* "$ROOT/tests/"

chmod +x "$ROOT/scripts/"*.sh "$ROOT/scripts/"*.py 2>/dev/null || true

export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python "$ROOT/scripts/phase54001_65000_verify.py"
python -m pytest -q "$ROOT/tests/test_phase54001_65000.py" --disable-warnings

if [ ! -f "$ROOT/.companyos_runtime/live_financial.env" ]; then
cat > "$ROOT/.companyos_runtime/live_financial.env" <<'EOF'
COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION=false
COMPANYOS_LIVE_MAX_SINGLE=0.001
COMPANYOS_LIVE_MAX_DAILY=0.005
COMPANYOS_LIVE_MIN_RESERVE=0.01
COMPANYOS_LIVE_REQUIRE_ALLOWLIST=true
EOF
chmod 600 "$ROOT/.companyos_runtime/live_financial.env"
fi

echo
echo "PHASE54001_65000_INSTALL_OK"
echo "LIVE_SIGNER_PATH=INTEGRATED"
echo "SOLANA_EXECUTION_GATE=INTEGRATED"
echo "ONE_SHOT_AUTHORIZATION=REQUIRED"
echo "TREASURY_LIMITS=REQUIRED"
echo "ALLOWLIST_REQUIRED_BY_DEFAULT=TRUE"
echo "KILL_SWITCH=REQUIRED"
echo "IDEMPOTENCY=REQUIRED"
echo "RECEIPT_RECONCILIATION=REQUIRED"
echo "POST_EXECUTION_LOCKOUT=REQUIRED"
echo "LIVE_EXECUTION_REQUIRES_EXPLICIT_ENABLE=TRUE"
echo "AUTONOMOUS_UNBOUNDED_SPENDING=FALSE"
echo
echo "Next:"
echo "  bash ~/companyos/scripts/companyos_live_final.sh status"
echo "  bash ~/companyos/scripts/companyos_live_final.sh enable-bounded"
echo "  bash ~/companyos/scripts/companyos_live_final.sh status"
