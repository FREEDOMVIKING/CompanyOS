#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.cicdops import CICDStatus
print(json.dumps(CICDStatus().status(),indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase14501_15000_verify.py"
    ;;
  cycle|demo)
    python "$ROOT/scripts/run_phase15000_cicd_demo.py"
    ;;
  *)
    echo "Usage: $0 {status|verify|cycle|demo}"
    exit 2
    ;;
esac
