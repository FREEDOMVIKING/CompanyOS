#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.expansionops import ExpansionOpsStatus
print(json.dumps(ExpansionOpsStatus().status(),indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase11001_11500_verify.py"
    ;;
  cycle|demo)
    python "$ROOT/scripts/run_phase11500_expansion_demo.py"
    ;;
  *)
    echo "Usage: $0 {status|verify|cycle|demo}"
    exit 2
    ;;
esac
