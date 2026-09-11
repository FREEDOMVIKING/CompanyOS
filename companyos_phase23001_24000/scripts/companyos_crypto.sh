#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  scan)
    python "$ROOT/scripts/companyos_wallet_scan.py"
    ;;
  bind)
    python "$ROOT/scripts/companyos_crypto_bind.py"
    ;;
  status)
    python "$ROOT/scripts/companyos_crypto_payments.py" status
    ;;
  verify)
    python "$ROOT/scripts/phase23001_24000_verify.py"
    ;;
  allowlist-show)
    cat "$ROOT/.companyos_runtime/crypto_destination_allowlist.json" 2>/dev/null || echo "[]"
    ;;
  *)
    echo "Usage: $0 {scan|bind|status|verify|allowlist-show}"
    exit 2
    ;;
esac
