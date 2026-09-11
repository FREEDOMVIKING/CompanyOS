import json, sys
from companyos.strategy.profit_first_execution_chain_repair import run_fanout

force = "--force" in sys.argv
print(json.dumps(run_fanout(force=force), indent=2, default=str))
