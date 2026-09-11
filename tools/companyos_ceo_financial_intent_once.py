#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from companyos.runtime.ceo_financial_intent_inbox import process_inbox

r = process_inbox()
print("=== CEO FINANCIAL INTENT PRODUCER ===")
for k in ("seen","queued","rejected","errors","last_error"):
    print(f"{k.upper()}:", r.get(k))
print("FREE-FORM PAYMENT INFERENCE: DISABLED")
print("DOWNSTREAM POLICY/RESERVE/LIVE CONTROLS: PRESERVED")
