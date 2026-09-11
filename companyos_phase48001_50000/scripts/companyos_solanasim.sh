#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  run)
    python "$ROOT/scripts/companyos_solana_simulation.py"
    ;;
  status)
    python - <<'PY'
import json
from companyos.solanasim import SolanaSimulationStatus
print(json.dumps(SolanaSimulationStatus().status(), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase48001_50000_verify.py"
    ;;
  *)
    echo "Usage: $0 {run|status|verify}"
    exit 2
    ;;
esac
