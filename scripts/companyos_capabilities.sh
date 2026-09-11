#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  status)
    python - <<'PY'
import json
from companyos.capabilityops import CapabilityOpsStatus, CapabilityRegistry, CredentialReadiness
reg=CapabilityRegistry().build()
print(json.dumps({
  "capabilities":CapabilityOpsStatus().status(),
  "credential_readiness":CredentialReadiness().evaluate(reg)
},indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase16001_16500_verify.py"
    ;;
  *)
    echo "Usage: $0 {status|verify}"
    exit 2
    ;;
esac
