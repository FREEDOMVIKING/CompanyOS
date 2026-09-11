#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from companyos.runtime.external_research_network_worker import run_cycle
r=run_cycle()
print("=== COMPANYOS EXTERNAL RESEARCH CYCLE ===")
for k in ("mode","available_mb","deferred","reason","sources_checked","raw_results","new_signals","duplicates","pipeline_accepted","pipeline_failed","last_error"):
    print(k.upper()+":",getattr(r,k))
print("EXTERNAL WRITE ACTIONS: DISABLED")
print("FINANCIAL ACTIONS: DISABLED")
