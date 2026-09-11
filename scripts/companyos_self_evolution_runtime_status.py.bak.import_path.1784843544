import json
from companyos.evolution.self_evolution_runtime_integration import load, STATE, LEDGER
rows=[]
if LEDGER.exists():
    for line in LEDGER.read_text(encoding='utf-8', errors='ignore').splitlines()[-100:]:
        try: rows.append(json.loads(line))
        except Exception: pass
print(json.dumps({'state':load(STATE,{}),'recent_runtime_integration_ledger':rows}, indent=2, default=str))
