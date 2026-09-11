#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
case "${1:-status}" in
 status) python - <<'PY'
import json
from companyos.venture_factory import VentureFactoryStatus
print(json.dumps(VentureFactoryStatus().status(),indent=2))
PY
 ;;
 cycle|demo) python "$ROOT/scripts/run_phase4000_venture_factory_demo.py";;
 verify) python "$ROOT/scripts/phase3501_4000_verify.py";;
 *) echo "Usage: $0 {status|cycle|demo|verify}"; exit 2;;
esac
