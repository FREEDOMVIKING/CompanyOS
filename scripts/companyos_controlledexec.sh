#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  demo)
    python "$ROOT/scripts/companyos_controlled_execution_demo.py"
    ;;
  status)
    python - <<'PY'
import json
from companyos.controlledexec import ControlledExecutionStatus
print(json.dumps(ControlledExecutionStatus().status(), indent=2))
PY
    ;;
  receipts)
    python - <<'PY'
import json
from pathlib import Path
from companyos.controlledexec import ControlledExecutionReceipt
print(json.dumps(ControlledExecutionReceipt(Path.home()/"companyos").recent(50), indent=2))
PY
    ;;
  lock-status)
    python - <<'PY'
import json
from pathlib import Path
from companyos.controlledexec import PostExecutionLock
print(json.dumps(PostExecutionLock(Path.home()/"companyos").status(), indent=2))
PY
    ;;
  unlock)
    python - <<'PY'
import json
from pathlib import Path
from companyos.controlledexec import PostExecutionLock
print(json.dumps(PostExecutionLock(Path.home()/"companyos").clear(), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase52001_54000_verify.py"
    ;;
  *)
    echo "Usage: $0 {demo|status|receipts|lock-status|unlock|verify}"
    exit 2
    ;;
esac
