#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.businessops import BusinessOpsStatus
print(json.dumps(BusinessOpsStatus().status(), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase27001_28000_verify.py"
    ;;
  demo)
    python "$ROOT/scripts/companyos_business_demo.py"
    ;;
  *)
    echo "Usage: $0 {status|verify|demo}"
    exit 2
    ;;
esac
