#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from companyos.resource_aware_financial_worker import run_resource_aware_once

r = run_resource_aware_once()
print("=== RESOURCE-AWARE FINANCIAL QUEUE ===")
print("MODE:", r.get("mode"))
print("AVAILABLE MB:", r.get("available_memory_mb"))
print("DEFERRED:", r.get("deferred"))
print("REASON:", r.get("reason"))
print("PROCESSED:", r.get("processed"))
print("FAILED:", r.get("failed"))
print("BROADCAST: NOT ENABLED")
