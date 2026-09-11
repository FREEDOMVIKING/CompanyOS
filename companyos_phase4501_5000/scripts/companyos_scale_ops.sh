#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.scaleops import ScaleOpsStatus
print(json.dumps(ScaleOpsStatus().status(),indent=2))
PY
    ;;
  cycle|demo)
    python "$ROOT/scripts/run_phase5000_scale_ops_demo.py"
    ;;
  verify)
    python "$ROOT/scripts/phase4501_5000_verify.py"
    ;;
  *)
    echo "Usage: $0 {status|cycle|demo|verify}"
    exit 2
    ;;
esac
