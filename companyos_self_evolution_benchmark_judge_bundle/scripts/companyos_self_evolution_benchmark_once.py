import json
from companyos.evolution.self_evolution_benchmark_judge import judge_recent_promotions
print(json.dumps(judge_recent_promotions(), indent=2, default=str))
