#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  demo)
    python "$ROOT/scripts/companyos_transaction_demo.py"
    ;;
  status)
    python - <<'PY'
import json
from companyos.transactionops import TransactionOpsStatus
print(json.dumps(TransactionOpsStatus().status(), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase46001_48000_verify.py"
    ;;
  *)
    echo "Usage: $0 {demo|status|verify}"
    exit 2
    ;;
esac
