#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

python scripts/companyos_production_readiness.py assess >/dev/null
python scripts/companyos_production_promoter.py promote >/dev/null
python scripts/companyos_revenue_operations.py build >/dev/null
python scripts/companyos_portfolio_feedback.py run >/dev/null
