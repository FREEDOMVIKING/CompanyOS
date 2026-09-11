#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  scan)
    python - <<'PY'
import json
from pathlib import Path
from companyos.walletautobind import ExistingWalletLocator
root=Path.home()/"companyos"
print(json.dumps({"success":True,"candidates":ExistingWalletLocator(root).scan()[:25]},indent=2))
PY
    ;;
  bind)
    python "$ROOT/scripts/companyos_wallet_autobind.py"
    ;;
  preflight)
    python "$ROOT/scripts/companyos_solana_preflight.py"
    ;;
  status)
    python - <<'PY'
import json
from companyos.walletautobind import WalletAutobindStatus
print(json.dumps(WalletAutobindStatus().status(),indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase40001_42000_verify.py"
    ;;
  *)
    echo "Usage: $0 {scan|bind|preflight|status|verify}"
    exit 2
    ;;
esac
