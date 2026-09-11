#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
case "${1:-status}" in
 status) python - <<'PY'
import json
from companyos.revenueops import RevenueOpsStatus
print(json.dumps(RevenueOpsStatus().status(),indent=2))
PY
 ;;
 verify) python "$ROOT/scripts/phase12501_13000_verify.py";;
 cycle|demo) python "$ROOT/scripts/run_phase13000_revenue_demo.py";;
 *) echo "Usage: $0 {status|verify|cycle|demo}"; exit 2;;
esac
