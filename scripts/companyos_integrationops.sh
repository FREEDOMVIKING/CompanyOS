#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.integrationops import IntegrationOpsStatus
print(json.dumps(IntegrationOpsStatus().status(), indent=2))
PY
    ;;
  demo)
    python "$ROOT/scripts/companyos_integrated_cycle_demo.py"
    ;;
  verify)
    python "$ROOT/scripts/phase34001_36000_verify.py"
    ;;
  *)
    echo "Usage: $0 {status|demo|verify}"
    exit 2
    ;;
esac
