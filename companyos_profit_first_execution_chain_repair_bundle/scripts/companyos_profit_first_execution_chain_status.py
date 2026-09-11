import json
from companyos.strategy.profit_first_execution_chain_repair import load, STATE, candidate_count
print(json.dumps({
    "candidate_count": candidate_count(),
    "state": load(STATE, {}),
}, indent=2, default=str))
