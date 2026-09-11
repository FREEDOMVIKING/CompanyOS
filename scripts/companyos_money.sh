#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python "$ROOT/scripts/companyos_multichain_money.py" status
    ;;
  readiness)
    python "$ROOT/scripts/companyos_multichain_money.py" readiness
    ;;
  verify)
    python "$ROOT/scripts/phase24001_25000_verify.py"
    ;;
  kill)
    python "$ROOT/scripts/companyos_multichain_money.py" kill
    ;;
  unkill)
    python "$ROOT/scripts/companyos_multichain_money.py" unkill
    ;;
  *)
    echo "Usage: $0 {status|readiness|verify|kill|unkill}"
    exit 2
    ;;
esac
