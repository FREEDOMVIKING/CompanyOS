#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from companyos.automatic_financial_queue_worker import run_once

r = run_once()
print("=== FINANCIAL QUEUE WORKER ===")
print("MODE:", r["mode"])
print("PENDING SEEN:", r["pending_seen"])
print("PROCESSED:", r["processed"])
print("FAILED:", r["failed"])
print("SKIPPED CLAIMED:", r["skipped_claimed"])
print("LAST ERROR:", r["last_error"])
