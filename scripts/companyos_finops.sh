#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.finops import FinOpsStatus
print(json.dumps(FinOpsStatus().status(), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase25001_26000_verify.py"
    ;;
  activation)
    cat "$ROOT/.companyos_runtime/financial_activation_state.json" 2>/dev/null || echo "NO_ACTIVATION_STATE"
    ;;
  *)
    echo "Usage: $0 {status|verify|activation}"
    exit 2
    ;;
esac
