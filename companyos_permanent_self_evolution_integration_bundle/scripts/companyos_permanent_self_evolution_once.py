import json
from companyos.evolution.permanent_self_evolution_integration import run_once
print(json.dumps(run_once(), indent=2, default=str))
