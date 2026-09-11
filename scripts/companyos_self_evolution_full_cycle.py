import json
from companyos.evolution.self_evolution_generator import run_once
from companyos.evolution.self_evolution_runtime_integration import run_once as integrate
print("===== GENERATOR =====")
print(json.dumps(run_once(),indent=2,default=str))
print("===== PROMOTION PIPELINE =====")
print(json.dumps(integrate(),indent=2,default=str))
