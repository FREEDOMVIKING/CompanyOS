#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.marketops import MarketOpsStatus
print(json.dumps(MarketOpsStatus().status(),indent=2))
PY
    ;;
  cycle|demo)
    python "$ROOT/scripts/run_phase4500_market_ops_demo.py"
    ;;
  verify)
    python "$ROOT/scripts/phase4001_4500_verify.py"
    ;;
  *)
    echo "Usage: $0 {status|cycle|demo|verify}"
    exit 2
    ;;
esac
