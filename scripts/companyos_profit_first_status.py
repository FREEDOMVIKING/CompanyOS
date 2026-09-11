import json
from companyos.strategy.profit_first_venture_engine import ensure_policy, discovery_directive
p = ensure_policy()
print(json.dumps({
  "mission": p["mission"],
  "business_model_neutral": p["business_model_neutral"],
  "minimum_candidates": p["minimum_candidates"],
  "minimum_unrelated_sectors": p["minimum_unrelated_sectors"],
  "minimum_business_model_families": p["minimum_business_model_families"],
  "minimum_investment_score": p["minimum_investment_score"],
  "max_active_validation_bets": p["max_active_validation_bets"],
  "no_build_below_threshold": p["no_build_below_threshold"],
  "portfolio_reallocation_enabled": p["portfolio_reallocation_enabled"]
}, indent=2))
print("\n--- ACTIVE DISCOVERY DIRECTIVE ---\n")
print(discovery_directive())
