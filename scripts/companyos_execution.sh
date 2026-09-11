#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
CMD="${1:-status}"

case "$CMD" in
  demo|cycle)
    python "$ROOT/scripts/run_phase3500_execution_demo.py"
    ;;
  verify)
    python "$ROOT/scripts/phase3001_3500_verify.py"
    ;;
  status)
    python - <<'PY'
import json
from companyos.execution import RuntimeStatus
print(json.dumps(RuntimeStatus().status(),indent=2))
PY
    ;;
  *)
    echo "Usage: $0 {demo|cycle|verify|status}"
    exit 2
    ;;
esac
