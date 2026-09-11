#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.resilienceops import ResilienceOpsStatus
print(json.dumps(ResilienceOpsStatus().status(),indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase11501_12000_verify.py"
    ;;
  cycle|demo)
    python "$ROOT/scripts/run_phase12000_resilience_demo.py"
    ;;
  *)
    echo "Usage: $0 {status|verify|cycle|demo}"
    exit 2
    ;;
esac
