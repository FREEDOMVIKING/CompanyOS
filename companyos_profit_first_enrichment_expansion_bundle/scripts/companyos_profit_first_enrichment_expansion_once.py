import json
from companyos.strategy.profit_first_enrichment_expansion import maybe_run
print(json.dumps(maybe_run(cooldown_seconds=0), indent=2, default=str))
