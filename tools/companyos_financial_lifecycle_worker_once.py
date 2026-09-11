#!/usr/bin/env python
from __future__ import annotations
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

import os

ENV = ROOT / ".env"
if ENV.exists():
    for line in ENV.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        os.environ[k] = v

from companyos.lifecycle_aware_financial_worker import process_lifecycle_once

r=process_lifecycle_once()
print("=== LIFECYCLE-AWARE FINANCIAL WORKER ===")
for k in ["mode","pending_seen","processed","failed","deferred_retry","skipped_claimed","last_error"]:
    print(k.upper()+":",r.get(k))
mode = str(r.get("mode", "dry_run")).lower()
print("BROADCAST REQUEST MODE:", "LIVE" if mode == "live" else "DRY_RUN")
