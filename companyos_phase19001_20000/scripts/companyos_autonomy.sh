#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.autonomyops import AutonomyOpsStatus
print(json.dumps(AutonomyOpsStatus().status(), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase19001_20000_verify.py"
    ;;
  run)
    shift
    python "$ROOT/scripts/companyos_autonomy.py" "$@"
    ;;
  *)
    echo "Usage: $0 {status|verify|run [--cycles N] [--objective TEXT] [--max-jobs N]}"
    exit 2
    ;;
esac
