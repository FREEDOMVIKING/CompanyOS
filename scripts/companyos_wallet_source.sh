#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
case "${1:-status}" in
  check) python "$ROOT/scripts/companyos_wallet_source_sync.py" ;;
  status) python - <<'PY'
import json
from companyos.walletsource import WalletSourceStatus
print(json.dumps(WalletSourceStatus().status(), indent=2))
PY
  ;;
  verify) python "$ROOT/scripts/phase45001_46000_verify.py" ;;
  *) echo "Usage: $0 {check|status|verify}"; exit 2 ;;
esac
