from companyos.governance.venture_identity_progression import evaluate_all, highest_priority_stalled
import json
print(json.dumps({"ventures": evaluate_all(), "highest_priority_stalled": highest_priority_stalled()}, indent=2, default=str))
