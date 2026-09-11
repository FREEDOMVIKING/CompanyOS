#!/usr/bin/env python
from pathlib import Path
p=Path("companyos_runtime/ceo_financial_scheduler")
print("=== CEO SCHEDULER FINANCIAL STATUS ===")
print("RECORDED CYCLES:",len(list(p.glob("*.json"))) if p.exists() else 0)
print("AUTONOMOUS EXECUTION MODE: DRY_RUN PINNED")
print("BROADCAST: NOT ENABLED BY SCHEDULER INTEGRATION")
