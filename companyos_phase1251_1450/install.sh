#!/data/data/com.termux/files/usr/bin/bash
set -e
TARGET="${1:-$HOME/companyos}"
SRC="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$TARGET"
cp -r "$SRC/companyos" "$TARGET/"
cp -r "$SRC/scripts" "$TARGET/"
cp -r "$SRC/tests" "$TARGET/"
cd "$TARGET"
export PYTHONPATH="$TARGET${PYTHONPATH:+:$PYTHONPATH}"
python -m py_compile companyos/departments/*.py
python -m pytest -q tests/test_phase1251_1450.py
echo "PHASE1251_1450_INSTALL_OK"
echo "EXECUTIVE_ORCHESTRATOR_READY"
echo "RESEARCH_DEPARTMENT_READY"
echo "PRODUCT_DEPARTMENT_READY"
echo "GROWTH_DEPARTMENT_READY"
echo "SALES_DEPARTMENT_READY"
echo "FINANCE_DEPARTMENT_READY"
echo "OPERATIONS_DEPARTMENT_READY"
echo "CUSTOMER_SUCCESS_DEPARTMENT_READY"
echo "LONG_TERM_EXECUTIVE_MEMORY_READY"
echo "CROSS_DEPARTMENT_COORDINATION_READY"
echo "HUMAN_AUTHORITY_GATES_READY"
