#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.treasuryops import TreasuryStatus
print(json.dumps(TreasuryStatus().status(), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase21001_22000_verify.py"
    ;;
  *)
    echo "Usage: $0 {status|verify}"
    exit 2
    ;;
esac
