import json
from companyos.strategy.research_output_candidate_materializer_v2 import materialize_all
print(json.dumps(materialize_all(), indent=2, default=str))
