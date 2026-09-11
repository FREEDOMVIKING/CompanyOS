#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  readiness)
    python "$ROOT/scripts/companyos_live_readiness.py"
    ;;
  status)
    python - <<'PY'
import json
from companyos.livegate import LiveGateStatus
print(json.dumps(LiveGateStatus().status(), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase50001_52000_verify.py"
    ;;
  *)
    echo "Usage: $0 {readiness|status|verify}"
    exit 2
    ;;
esac
