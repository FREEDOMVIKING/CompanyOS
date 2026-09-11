#!/usr/bin/env python

from __future__ import annotations

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from companyos.runtime_financial_queue import enqueue, pending_items

ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)

e = sub.add_parser("enqueue")
e.add_argument("--action-type", default="sol_transfer")
e.add_argument("--destination", required=True)
e.add_argument("--sol", required=True, type=float)
e.add_argument("--source-ref", default="")
e.add_argument("--idempotency-key", default=None)

sub.add_parser("list")

args = ap.parse_args()

if args.cmd == "enqueue":
    item = enqueue(
        action_type=args.action_type,
        destination=args.destination,
        sol=args.sol,
        source_ref=args.source_ref,
        idempotency_key=args.idempotency_key,
    )
    print("QUEUED:", item.queue_id)
    print("IDEMPOTENCY:", item.idempotency_key)
    print("MODE: QUEUE ONLY")
elif args.cmd == "list":
    items = pending_items()
    print("PENDING:", len(items))
    for i in items:
        print(i.queue_id, i.action_type, i.destination, i.sol, i.idempotency_key)
