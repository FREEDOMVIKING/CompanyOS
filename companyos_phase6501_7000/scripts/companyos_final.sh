#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
case "${1:-status}" in
 status)
  python - <<'PY'
import json
from companyos.finalops import FinalOpsStatus
print(json.dumps(FinalOpsStatus().status(),indent=2))
PY
 ;;
 verify) python "$ROOT/scripts/phase6501_7000_verify.py" ;;
 cycle|readiness) python "$ROOT/scripts/run_phase7000_final_demo.py" ;;
 *) echo "Usage: $0 {status|verify|cycle|readiness}"; exit 2 ;;
esac
