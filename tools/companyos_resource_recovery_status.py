#!/usr/bin/env python
from __future__ import annotations
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from companyos.resource_aware_financial_worker import load_status, mem_available_mb

print("=== COMPANYOS RESOURCE RECOVERY STATUS ===")
print("AVAILABLE MEMORY MB:", mem_available_mb())
print(json.dumps(load_status(), indent=2, sort_keys=True))
