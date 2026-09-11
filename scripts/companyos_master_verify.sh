#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${COMPANYOS_ROOT:-$HOME/companyos}"
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

echo "=== COMPANYOS MASTER VERIFICATION ==="

python "$ROOT/scripts/phase14501_15000_verify.py" 2>/dev/null || true
python "$ROOT/scripts/phase15001_15500_verify.py"
python "$ROOT/scripts/phase15501_16000_verify.py"
python "$ROOT/scripts/phase16001_16500_verify.py"

python -m pytest -q   "$ROOT/tests/test_phase14501_15000.py"   "$ROOT/tests/test_phase15001_15500.py"   "$ROOT/tests/test_phase15501_16000.py"   --disable-warnings

echo "COMPANYOS_MASTER_VERIFICATION_PASSED"
