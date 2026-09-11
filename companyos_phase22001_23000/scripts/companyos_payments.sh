#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.paymentops import PaymentOpsStatus
print(json.dumps(PaymentOpsStatus().status(), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase22001_23000_verify.py"
    ;;
  demo)
    python "$ROOT/scripts/companyos_payment_demo.py"
    ;;
  approvals)
    python - <<'PY'
import json
from pathlib import Path
from companyos.paymentops import PaymentApprovalQueue
q = PaymentApprovalQueue(Path.home() / "companyos")
print(json.dumps(q.pending(), indent=2))
PY
    ;;
  *)
    echo "Usage: $0 {status|verify|demo|approvals}"
    exit 2
    ;;
esac
