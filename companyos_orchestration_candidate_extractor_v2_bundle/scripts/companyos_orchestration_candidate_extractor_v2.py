import json, sys
from companyos.strategy.orchestration_candidate_extractor_v2 import extract_for_orchestration

oid = sys.argv[1] if len(sys.argv) > 1 else None
r = extract_for_orchestration(oid)
print(json.dumps(r, indent=2, default=str))
