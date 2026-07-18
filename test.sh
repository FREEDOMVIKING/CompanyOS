#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Running CompanyOS tests..."

python "$ROOT_DIR/companyos/tests/test_core.py"
bash "$ROOT_DIR/companyos/verify.sh"

echo
echo "ALL COMPANYOS TESTS PASSED"
