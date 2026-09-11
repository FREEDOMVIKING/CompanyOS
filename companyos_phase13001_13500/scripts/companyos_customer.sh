#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
case "${1:-status}" in
 status) python - <<'PY'
import json
from companyos.customerops import CustomerOpsStatus
print(json.dumps(CustomerOpsStatus().status(),indent=2))
PY
 ;;
 verify) python "$ROOT/scripts/phase13001_13500_verify.py";;
 cycle|demo) python "$ROOT/scripts/run_phase13500_customer_demo.py";;
 *) echo "Usage: $0 {status|verify|cycle|demo}"; exit 2;;
esac
