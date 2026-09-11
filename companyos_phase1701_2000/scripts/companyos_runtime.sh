#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
CMD="${1:-status}"

case "$CMD" in
  cycle)
    python "$ROOT/scripts/run_phase2000_runtime_demo.py"
    ;;
  verify)
    python "$ROOT/scripts/phase1701_2000_verify.py"
    ;;
  status)
    python - <<'PY'
import json
from pathlib import Path
from companyos.runtime import CEOCompanyRuntime
print(json.dumps(CEOCompanyRuntime(Path.home()/"companyos").status(), indent=2))
PY
    ;;
  recover)
    python - <<'PY'
import json
from pathlib import Path
from companyos.runtime import CEOCompanyRuntime
print(json.dumps(CEOCompanyRuntime(Path.home()/"companyos").recover(), indent=2))
PY
    ;;
  *)
    echo "Usage: $0 {cycle|verify|status|recover}"
    exit 2
    ;;
esac
