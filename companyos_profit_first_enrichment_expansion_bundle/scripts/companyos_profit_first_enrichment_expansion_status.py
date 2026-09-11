import json
from companyos.strategy.profit_first_enrichment_expansion import current_summary, load, STATE, REPORT
print(json.dumps({
    "current_summary": current_summary(),
    "controller_state": load(STATE, {}),
    "last_report": load(REPORT, {}),
}, indent=2, default=str))
