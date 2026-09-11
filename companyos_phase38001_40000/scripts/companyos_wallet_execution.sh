#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.walletintegration import WalletIntegrationStatus
print(json.dumps(WalletIntegrationStatus().status(), indent=2))
PY
    ;;
  readiness)
    python "$ROOT/scripts/companyos_wallet_execution_readiness.py"
    ;;
  verify)
    python "$ROOT/scripts/phase38001_40000_verify.py"
    ;;
  kill)
    python - <<'PY'
import json
from pathlib import Path
from companyos.moneyops import FinancialKillSwitch
print(json.dumps(FinancialKillSwitch(Path.home()/ "companyos").engage("manual_cli"), indent=2))
PY
    ;;
  unkill)
    python - <<'PY'
import json
from pathlib import Path
from companyos.moneyops import FinancialKillSwitch
print(json.dumps(FinancialKillSwitch(Path.home()/ "companyos").clear(), indent=2))
PY
    ;;
  *)
    echo "Usage: $0 {status|readiness|verify|kill|unkill}"
    exit 2
    ;;
esac
