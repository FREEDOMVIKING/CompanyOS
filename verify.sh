#!/data/data/com.termux/files/usr/bin/bash

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ERRORS=0
WARNINGS=0

pass() {
    echo "[PASS] $1"
}

fail() {
    echo "[FAIL] $1"
    ERRORS=$((ERRORS + 1))
}

warn() {
    echo "[WARN] $1"
    WARNINGS=$((WARNINGS + 1))
}

echo "============================================================"
echo " CompanyOS Verification"
echo " Root: $ROOT_DIR"
echo "============================================================"

echo
echo "Checking core files..."

for FILE in \
    company_cycle.py \
    company_manager.py \
    ceo_company.py
do
    if [ -f "$ROOT_DIR/$FILE" ]; then
        pass "$FILE exists"
    else
        fail "$FILE is missing"
    fi
done

echo
echo "Checking core directories..."

for DIR in \
    agents \
    ceo_memory \
    companyos
do
    if [ -d "$ROOT_DIR/$DIR" ]; then
        pass "$DIR exists"
    else
        fail "$DIR is missing"
    fi
done

echo
echo "Checking Python syntax..."

PYTHON_FILES=(
    "$ROOT_DIR/company_cycle.py"
    "$ROOT_DIR/company_manager.py"
    "$ROOT_DIR/ceo_company.py"
)

for FILE in "$ROOT_DIR"/agents/*.py; do
    [ -e "$FILE" ] && PYTHON_FILES+=("$FILE")
done

for FILE in "${PYTHON_FILES[@]}"; do
    if [ ! -f "$FILE" ]; then
        continue
    fi

    if python -m py_compile "$FILE" >/dev/null 2>&1; then
        pass "Syntax valid: ${FILE#$ROOT_DIR/}"
    else
        fail "Syntax error: ${FILE#$ROOT_DIR/}"
    fi
done

echo
echo "Checking JSON memory files..."

for FILE in "$ROOT_DIR"/ceo_memory/*.json; do
    [ -e "$FILE" ] || continue

    if python - "$FILE" <<'PY' >/dev/null 2>&1
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
json.loads(path.read_text(encoding="utf-8"))
PY
    then
        pass "JSON valid: ${FILE#$ROOT_DIR/}"
    else
        fail "Invalid JSON: ${FILE#$ROOT_DIR/}"
    fi
done

echo
echo "Checking installed agents..."

EXPECTED_AGENTS=(
    research_agent.py
    builder_agent.py
    auditor_agent.py
    marketing_agent.py
    finance_agent.py
    recovery_agent.py
    executive_agent.py
    learning_agent.py
    scoring_agent.py
)

for AGENT in "${EXPECTED_AGENTS[@]}"; do
    if [ -f "$ROOT_DIR/agents/$AGENT" ]; then
        pass "Agent installed: $AGENT"
    else
        warn "Agent not found: $AGENT"
    fi
done

echo
echo "============================================================"
echo " Verification complete"
echo " Errors: $ERRORS"
echo " Warnings: $WARNINGS"
echo "============================================================"

if [ "$ERRORS" -gt 0 ]; then
    exit 1
fi
