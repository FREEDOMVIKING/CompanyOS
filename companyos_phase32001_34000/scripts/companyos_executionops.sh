#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.executionops import ExecutionOpsStatus
print(json.dumps(ExecutionOpsStatus().status(), indent=2))
PY
    ;;
  scan)
    python "$ROOT/scripts/companyos_execution_scan.py"
    ;;
  demo)
    python "$ROOT/scripts/companyos_execution_demo.py"
    ;;
  receipts)
    python - <<'PY'
import json
from pathlib import Path
from companyos.executionops import ExecutionReceiptStore
print(json.dumps(ExecutionReceiptStore(Path.home()/ "companyos").recent(50), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase32001_34000_verify.py"
    ;;
  *)
    echo "Usage: $0 {status|scan|demo|receipts|verify}"
    exit 2
    ;;
esac
