import json
from companyos.evolution.self_evolution_promotion_engine import discover, ledger, load, STATE

print(json.dumps({
    "generated_candidates": discover()[:50],
    "state": load(STATE, {}),
    "recent_evolution_ledger": ledger(50),
}, indent=2, default=str))
