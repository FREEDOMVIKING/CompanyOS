from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from companyos.evolution.self_evolution_runtime_integration import load, STATE, LEDGER

# Check if the ledger has already been processed
if LEDGER.exists():
    print("Ledger has already been processed.")
else:
    rows = []
    for line in LEDGER.read_text(encoding='utf-8', errors='ignore').splitlines()[-100:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    print(json.dumps({'state': load(STATE, {}), 'recent_runtime_integration_ledger': rows}, indent=2, default=str))
