#!/usr/bin/env python
from __future__ import annotations
import os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
env=ROOT/".env"
if env.exists():
    for line in env.read_text(errors="ignore").splitlines():
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k,v=line.split("=",1); os.environ[k.strip()]=v.strip().strip('"').strip("'")
from companyos.runtime.ceo_scheduler_financial_integration import run_scheduler_financial_cycle
r=run_scheduler_financial_cycle(cycle_id=f"manual-safe-{int(time.time())}",metadata={"source":"manual_safe_validation"})
print("=== CEO SCHEDULER FINANCIAL INTEGRATION ===")
for k in ("mode","accepted","deduplicated","reason"): print(k.upper()+":",r.get(k))
print("BROADCAST: NOT ENABLED BY THIS INTEGRATION")
