import json
from companyos.evolution.self_evolution_generator import detect_gaps,load,STATE
print(json.dumps({"detected_gaps":detect_gaps(),"state":load(STATE,{})},indent=2,default=str))
