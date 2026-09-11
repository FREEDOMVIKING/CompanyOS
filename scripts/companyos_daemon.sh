#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.daemonops import AutonomousRuntimeStatus
print(json.dumps(AutonomousRuntimeStatus().status(),indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase15001_15500_verify.py"
    ;;
  tick|cycle|demo)
    python "$ROOT/scripts/run_phase15500_daemon_demo.py"
    ;;
  *)
    echo "Usage: $0 {status|verify|tick|cycle|demo}"
    exit 2
    ;;
esac
