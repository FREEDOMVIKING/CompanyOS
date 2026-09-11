#!/usr/bin/env python
from pathlib import Path
import json
p=Path("companyos_runtime/external_research_network/state.json")
print("=== COMPANYOS EXTERNAL RESEARCH STATUS ===")
if not p.exists():print("STATE: NOT RUN YET")
else:
    try:
        d=json.loads(p.read_text())
        for k,v in d.items():print(k.upper()+":",v)
    except Exception as e:print("STATE ERROR:",type(e).__name__)
print("EXTERNAL WRITE ACTIONS: DISABLED")
print("FINANCIAL ACTIONS: DISABLED")
