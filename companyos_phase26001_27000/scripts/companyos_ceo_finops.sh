#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.ceofinops import CEOFinOpsStatus
print(json.dumps(CEOFinOpsStatus().status(), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase26001_27000_verify.py"
    ;;
  demo)
    python "$ROOT/scripts/companyos_ceo_finance_demo.py"
    ;;
  *)
    echo "Usage: $0 {status|verify|demo}"
    exit 2
    ;;
esac
