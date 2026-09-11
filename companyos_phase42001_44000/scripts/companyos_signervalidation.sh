#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-status}" in
  validate)
    python "$ROOT/scripts/companyos_signer_validation.py"
    ;;
  status)
    python - <<'PY'
import json
from companyos.signervalidation import SignerValidationStatus
print(json.dumps(SignerValidationStatus().status(), indent=2))
PY
    ;;
  report)
    cat "$ROOT/.companyos_runtime/signer_validation_report.json" 2>/dev/null || echo "NO_REPORT"
    ;;
  verify)
    python "$ROOT/scripts/phase42001_44000_verify.py"
    ;;
  *)
    echo "Usage: $0 {validate|status|report|verify}"
    exit 2
    ;;
esac
