#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

python scripts/companyos_opportunity_discovery.py cycle >/dev/null
python scripts/companyos_research_planning_engine.py process >/dev/null
python scripts/companyos_agent_orchestrator.py process >/dev/null
python scripts/companyos_venture_execution_director.py process
python scripts/companyos_milestone_executor.py process
