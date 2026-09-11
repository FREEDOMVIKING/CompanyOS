#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.actiongov import ActionGovernanceStatus
print(json.dumps(ActionGovernanceStatus().status(),indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase9001_9500_verify.py"
    ;;
  cycle|demo)
    python "$ROOT/scripts/run_phase9500_action_governance_demo.py"
    ;;
  *)
    echo "Usage: $0 {status|verify|cycle|demo}"
    exit 2
    ;;
esac
