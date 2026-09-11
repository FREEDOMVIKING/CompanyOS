#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.capabilityops import CapabilityOpsStatus
print(json.dumps(CapabilityOpsStatus().status(), indent=2))
PY
    ;;
  scan)
    python "$ROOT/scripts/companyos_capability_scan.py"
    ;;
  demo)
    python "$ROOT/scripts/companyos_capability_demo.py"
    ;;
  verify)
    python "$ROOT/scripts/phase30001_32000_verify.py"
    ;;
  *)
    echo "Usage: $0 {status|scan|demo|verify}"
    exit 2
    ;;
esac
