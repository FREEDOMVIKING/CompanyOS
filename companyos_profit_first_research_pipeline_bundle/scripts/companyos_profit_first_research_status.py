import json
from companyos.strategy.profit_first_research_pipeline import evidence_summary, load, STATE
print(json.dumps({
    "evidence_summary": evidence_summary(),
    "research_pipeline_state": load(STATE, {}),
    "candidate_directory": ".companyos_runtime/profit_first_candidates"
}, indent=2, default=str))
