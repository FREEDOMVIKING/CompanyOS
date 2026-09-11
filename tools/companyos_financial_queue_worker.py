#!/usr/bin/env python

from __future__ import annotations

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from dataclasses import asdict, is_dataclass

from companyos.runtime_financial_queue import pending_items, claim, release, complete

def normalize(obj):
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    return {"value": str(obj)}

def dispatch_dry_run(item):
    # Existing dispatcher installed by the previous bundle.
    from companyos_scheduler_finance import dispatch_scheduler_financial_intent
    return dispatch_scheduler_financial_intent(
        action_type=item.action_type,
        destination=item.destination,
        sol=item.sol,
        allow_broadcast=False,
        confirm_token="",
        idempotency_key=item.idempotency_key,
    )

ap = argparse.ArgumentParser()
ap.add_argument("--once", action="store_true", default=True)
args = ap.parse_args()

items = pending_items()
print("QUEUE PENDING:", len(items))

processed = 0
for item in items:
    if not claim(item):
        print("SKIP CLAIMED:", item.idempotency_key)
        continue
    try:
        result = dispatch_dry_run(item)
        data = normalize(result)
        # A dry-run can safely be finalized because the idempotency record
        # describes this exact non-broadcast attempt.
        complete(item, data)
        processed += 1
        print("DRY RUN COMPLETE:", item.idempotency_key)
        print("BROADCAST: NOT REQUESTED")
    except Exception as exc:
        release(item)
        print("DRY RUN FAILED:", item.idempotency_key, type(exc).__name__, str(exc)[:200])

print("PROCESSED:", processed)
