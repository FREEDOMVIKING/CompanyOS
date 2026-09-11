#!/usr/bin/env python
from __future__ import annotations
import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from companyos.automatic_financial_queue_worker import load_status
print(json.dumps(load_status(), indent=2, sort_keys=True))
