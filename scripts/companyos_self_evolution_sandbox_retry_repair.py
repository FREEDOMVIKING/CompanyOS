import json
from companyos.evolution.self_evolution_sandbox_retry_repair import run_repair_cycle
print(json.dumps(run_repair_cycle(), indent=2, default=str))
