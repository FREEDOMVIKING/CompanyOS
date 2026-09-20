#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS V23 DURABLE RECOVERY + CONTINUOUS ADVANCE ====="

test -f companyos/runtime/durable_execution_closure.py
cp -f companyos/runtime/durable_execution_closure.py ".companyos_runtime/durable_execution_closure.py.v22.$(date +%s).bak"

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/durable_execution_closure.py")
s=p.read_text()
insert=r