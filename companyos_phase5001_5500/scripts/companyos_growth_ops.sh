#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
case "${1:-status}" in
 status)
  python - <<'PY'
import json
from companyos.growthops import GrowthOpsStatus
print(json.dumps(GrowthOpsStatus().status(),indent=2))
PY
 ;;
 cycle|demo) python "$ROOT/scripts/run_phase5500_growth_ops_demo.py" ;;
 verify) python "$ROOT/scripts/phase5001_5500_verify.py" ;;
 *) echo "Usage: $0 {status|cycle|demo|verify}"; exit 2 ;;
esac
