import json
from companyos.evolution.self_evolution_generator import run_once
print(json.dumps(run_once(),indent=2,default=str))
