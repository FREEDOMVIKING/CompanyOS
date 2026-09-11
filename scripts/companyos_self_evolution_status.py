from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from companyos.evolution.self_evolution_promotion_engine import discover, ledger, load, STATE

print(json.dumps({
    "generated_candidates": discover()[:50],
    "state": load(STATE, {}),
    "recent_evolution_ledger": ledger(50),
}, indent=2, default=str))
