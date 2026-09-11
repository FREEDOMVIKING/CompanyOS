#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.ceointelligence import CEOIntelligenceStatus
print(json.dumps(CEOIntelligenceStatus().status(), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase16501_17000_verify.py"
    ;;
  run)
    shift
    python "$ROOT/scripts/companyos_ceo.py" "$@"
    ;;
  plan)
    shift
    python "$ROOT/scripts/companyos_ceo.py" --plan-only "$@"
    ;;
  *)
    echo "Usage: $0 {status|verify|run [objective]|plan [objective]}"
    exit 2
    ;;
esac
