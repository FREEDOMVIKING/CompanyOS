#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

python scripts/companyos_opportunity_discovery.py cycle >/dev/null
python scripts/companyos_research_planning_engine.py process
python scripts/companyos_agent_orchestrator.py process
