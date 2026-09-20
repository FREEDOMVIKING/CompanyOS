#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export GIT_PAGER=cat
export PAGER=cat

echo "===== COMPANYOS V65.54B TERMUX-SAFE FULL SUITE SCAN ====="
echo "SOURCE_WRITES=0"

WORKDIR="$HOME/.companyos_runtime/tmp"
REPORT_DIR="$HOME/.companyos_runtime/reports"
mkdir -p "$WORKDIR" "$REPORT_DIR"

PYTEST_OUT="$WORKDIR/v65_54b_pytest_$(date +%s).out"
REPORT="$REPORT_DIR/v65_54b_next_failure_$(date +%s).txt"

echo "PYTEST_OUT=$PYTEST_OUT"
echo "REPORT=$REPORT"

echo "===== GIT STATUS ====="
git --no-pager status --short || true

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
python -m pytest -q -x >"$PYTEST_OUT" 2>&1
RC=$?
set -e

echo "FULL_SUITE_RETURN_CODE=$RC"
echo "===== PYTEST TAIL ====="
tail -n 180 "$PYTEST_OUT" || true

{
  echo "V65.54B CompanyOS Termux-safe full-suite scan"
  echo "timestamp=$(date -Iseconds)"
  echo "full_suite_return_code=$RC"
  echo
  echo "===== git status ====="
  git --no-pager status --short || true
  echo
  echo "===== pytest tail ====="
  tail -n 260 "$PYTEST_OUT" || true
} > "$REPORT"

echo "REPORT_WRITTEN=$REPORT"

if [ "$RC" -eq 0 ]; then
  echo "FULL_SUITE=PASS"
  echo "V65_54B_READY_FOR_CHECKPOINT=TRUE"
else
  echo "FULL_SUITE=NEXT_FAILURE_FOUND"
  echo "V65_54B_READY_FOR_CHECKPOINT=CAPABILITY_ONLY"
fi

echo "V65_54B_COMPLETE"
