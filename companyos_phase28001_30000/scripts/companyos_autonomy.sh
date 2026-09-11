#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
case "${1:-status}" in
 status) python - <<'PY'
import json
from companyos.autonomy import AutonomyStatus
print(json.dumps(AutonomyStatus().status(),indent=2))
PY
 ;;
 verify) python "$ROOT/scripts/phase28001_30000_verify.py";;
 demo|cycle) python "$ROOT/scripts/companyos_autonomy_demo.py";;
 *) echo "Usage: $0 {status|verify|demo|cycle}"; exit 2;;
esac
