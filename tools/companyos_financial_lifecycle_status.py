#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from companyos.financial_intent_lifecycle import FinancialIntentLifecycleStore

store=FinancialIntentLifecycleStore()
records=store.list_records()

print("=== FINANCIAL INTENT LIFECYCLE STATUS ===")
print("RECORDS:",len(records))
counts={}
for r in records:
    counts[r.state]=counts.get(r.state,0)+1
print("COUNTS:",counts)

for r in records[-10:]:
    print(
        r.lifecycle_id,
        "|",r.state,
        "| attempts=",r.attempt_count,
        "| sol=",r.sol,
        "| error=",r.last_error or "NONE",
    )
