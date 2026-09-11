#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.recoveryops import RecoveryOpsStatus
print(json.dumps(RecoveryOpsStatus().status(), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase20001_21000_verify.py"
    ;;
  *)
    echo "Usage: $0 {status|verify}"
    exit 2
    ;;
esac
