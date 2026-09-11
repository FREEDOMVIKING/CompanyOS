#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.cycleops import CycleOpsStatus
print(json.dumps(CycleOpsStatus().status(), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase18001_19000_verify.py"
    ;;
  *)
    echo "Usage: $0 {status|verify}"
    exit 2
    ;;
esac
