#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
source "$HOME/.companyos_launch_env" 2>/dev/null || true

echo "=== CompanyOS Candidate Intelligence + Qualification Repair ==="
TS="$(date +%Y%m%d_%H%M%S)"
BK="$HOME/companyos_backups/candidate_intelligence_$TS"
mkdir -p "$BK"
cp companyos/runtime/profit_opportunity_engine.py "$BK/" 2>/dev/null || true

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/profit_opportunity_engine.py")
s=p.read_text()
if "COMPANYOS_CANDIDATE_INTELLIGENCE_V1" not in s:
    s += r