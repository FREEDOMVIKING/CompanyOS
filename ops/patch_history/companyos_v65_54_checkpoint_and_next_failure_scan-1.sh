#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.54 CHECKPOINT + NEXT-FAILURE SCAN ====="
echo "SOURCE_WRITES=0"

echo "===== GIT STATUS ====="
git status --short || true

echo "===== CAPABILITY EXPANSION DIFF ====="
git diff -- companyos/runtime/capability_expansion.py || true

echo "===== COMPILE GATE ====="
python -m py_compile companyos/runtime/capability_expansion.py
echo "CAPABILITY_SOURCE_COMPILE=PASS"

echo "===== CAPABILITY SUBSYSTEM RECHECK ====="
python -m pytest -q \
  tests/test_capability_expansion.py \
  tests/test_capability_expansion_generation_recovery_v6.py \
  tests/test_capability_expansion_staging_v4.py \
  tests/test_capability_expansion_test_recovery_v5.py \
  tests/test_capability_expansion_v3.py
echo "CAPABILITY_SUBSYSTEM=PASS"

echo "===== FULL SUITE NEXT-FAILURE SCAN ====="
set +e
python -m pytest -q -x > /tmp/companyos_v65_54_pytest.out 2>&1
RC=$?
set -e

tail -n 140 /tmp/companyos_v65_54_pytest.out || true
echo "FULL_SUITE_RETURN_CODE=$RC"

REPORT_DIR="$HOME/.companyos_runtime/reports"
mkdir -p "$REPORT_DIR"
REPORT="$REPORT_DIR/v65_54_next_failure_$(date +%s).txt"
{
  echo "V65.54 CompanyOS checkpoint + next-failure scan"
  echo "timestamp=$(date -Iseconds)"
  echo "full_suite_return_code=$RC"
  echo
  echo "===== git status ====="
  git status --short || true
  echo
  echo "===== capability expansion diff ====="
  git diff -- companyos/runtime/capability_expansion.py || true
  echo
  echo "===== pytest tail ====="
  tail -n 220 /tmp/companyos_v65_54_pytest.out || true
} > "$REPORT"

echo "REPORT=$REPORT"

if [ "$RC" -eq 0 ]; then
  echo "FULL_SUITE=PASS"
  echo "V65_54_READY_FOR_CHECKPOINT=TRUE"
else
  echo "FULL_SUITE=NEXT_FAILURE_FOUND"
  echo "V65_54_READY_FOR_CHECKPOINT=CAPABILITY_ONLY"
fi

echo "V65_54_COMPLETE"
