import json
from companyos.strategy.candidate_materialization_bridge import materialize, maybe_recover_missing_outputs

m = materialize()
print("===== MATERIALIZATION =====")
print(json.dumps(m, indent=2, default=str))

r = maybe_recover_missing_outputs(min_expected_candidates=1, cooldown_seconds=300)
print("===== RECOVERY =====")
print(json.dumps(r, indent=2, default=str))
