COMPANYOS PROFIT-FIRST EXECUTION CHAIN REPAIR

Purpose:
Repair the confirmed broken chain:
root_goal_created -> no delegated research outputs -> no structured candidates

This bundle does not fake candidate data.
Instead, it explicitly fans the research mission out into 7 focused specialist research orchestrations,
each with a direct file-output contract.

Each batch must:
- produce at least 4 materially distinct candidates
- write structured JSON directly into .companyos_runtime/profit_first_candidates/
- write a batch summary
- use 0-100 evidence/economic scores
- avoid duplicate/versioned construction-heavy variants
- preserve all existing safety/approval/financial gates

INSTALL

cd ~/companyos || exit 1

rm -rf companyos_profit_first_execution_chain_repair_bundle
mkdir -p companyos_profit_first_execution_chain_repair_bundle

unzip -o ~/storage/downloads/COMPANYOS_PROFIT_FIRST_EXECUTION_CHAIN_REPAIR_BUNDLE.zip   -d ~/companyos/companyos_profit_first_execution_chain_repair_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_profit_first_execution_chain_repair_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_profit_first_execution_chain_repair_bundle/verify.py

Run the fanout repair:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_execution_chain_repair.py

Wait 60-120 seconds, then:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_candidate_materialization.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_extract_canonical_research_outputs.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_evidence.py

Check repair state:

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_profit_first_execution_chain_status.py
