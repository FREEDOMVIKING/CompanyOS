#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
CMD="${1:-status}"

case "$CMD" in
  demo|cycle)
    python "$ROOT/scripts/run_phase3000_controlplane_demo.py"
    ;;
  verify)
    python "$ROOT/scripts/phase2601_3000_verify.py"
    ;;
  status)
    python - <<'PY'
import json
from companyos.controlplane import RuntimeStatus
print(json.dumps(RuntimeStatus().status(),indent=2))
PY
    ;;
  *)
    echo "Usage: $0 {demo|cycle|verify|status}"
    exit 2
    ;;
esac
