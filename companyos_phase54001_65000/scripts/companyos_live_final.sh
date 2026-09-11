#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
ENVFILE="$ROOT/.companyos_runtime/live_financial.env"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p "$ROOT/.companyos_runtime"

load_env() {
  if [ -f "$ENVFILE" ]; then
    set -a
    . "$ENVFILE"
    set +a
  fi
}

case "${1:-status}" in
  status)
    load_env
    python "$ROOT/scripts/companyos_live_final.py"
    ;;
  enable-bounded)
    cat > "$ENVFILE" <<'EOF'
COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION=true
COMPANYOS_LIVE_MAX_SINGLE=0.001
COMPANYOS_LIVE_MAX_DAILY=0.005
COMPANYOS_LIVE_MIN_RESERVE=0.01
COMPANYOS_LIVE_REQUIRE_ALLOWLIST=true
EOF
    chmod 600 "$ENVFILE"
    echo "BOUNDED_LIVE_MODE_CONFIGURED"
    echo "max_single=0.001"
    echo "max_daily=0.005"
    echo "min_reserve=0.01"
    echo "allowlist_required=true"
    ;;
  disable)
    cat > "$ENVFILE" <<'EOF'
COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION=false
COMPANYOS_LIVE_MAX_SINGLE=0.001
COMPANYOS_LIVE_MAX_DAILY=0.005
COMPANYOS_LIVE_MIN_RESERVE=0.01
COMPANYOS_LIVE_REQUIRE_ALLOWLIST=true
EOF
    chmod 600 "$ENVFILE"
    echo "LIVE_FINANCIAL_EXECUTION_DISABLED"
    ;;
  verify)
    python "$ROOT/scripts/phase54001_65000_verify.py"
    ;;
  *)
    echo "Usage: $0 {status|enable-bounded|disable|verify}"
    exit 2
    ;;
esac
