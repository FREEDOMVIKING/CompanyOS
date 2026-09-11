#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  detect|probe)
    python "$ROOT/scripts/companyos_signer_compat.py"
    ;;
  report)
    cat "$ROOT/.companyos_runtime/signer_compatibility_report.json" 2>/dev/null || echo "NO_REPORT"
    ;;
  status)
    python - <<'PY'
import json
from companyos.signercompat import SignerCompatStatus
print(json.dumps(SignerCompatStatus().status(), indent=2))
PY
    ;;
  verify)
    python "$ROOT/scripts/phase44001_45000_verify.py"
    ;;
  *)
    echo "Usage: $0 {detect|probe|report|status|verify}"
    exit 2
    ;;
esac
