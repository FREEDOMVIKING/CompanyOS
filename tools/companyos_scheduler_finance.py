#!/usr/bin/env python3
from pathlib import Path
import argparse, sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from companyos.runtime_bootstrap import load_dotenv
load_dotenv(ROOT)
from companyos.runtime.scheduler_financial_entrypoint import dispatch_scheduler_financial_intent

ap=argparse.ArgumentParser()
ap.add_argument("--destination", required=True)
ap.add_argument("--sol", required=True, type=float)
ap.add_argument("--action-id", default="")
ap.add_argument("--source", default="scheduler_cli")
ap.add_argument("--live", action="store_true")
ap.add_argument("--confirm-token", default="")
args=ap.parse_args()

r=dispatch_scheduler_financial_intent({
    "destination": args.destination,
    "amount_sol": args.sol,
    "action_id": args.action_id,
    "source": args.source,
    "requested_mode": "live" if args.live else "dry_run",
    "confirm_token": args.confirm_token,
    "metadata": {"invoked_via":"scheduler_finance_cli"},
})

print("=== SCHEDULER FINANCIAL INTENT RESULT ===")
print("ACTION ID:", r.action_id)
print("MODE:", r.requested_mode)
print("ACCEPTED:", r.accepted)
print("REASON:", r.reason)
print("STATE:", r.state or "NONE")
print("SIGNATURE:", r.signature or "NONE")
print("CONFIRMATION:", r.confirmation_status or "NONE")
print("LIFECYCLE ID:", r.lifecycle_id or "NONE")
raise SystemExit(0 if r.accepted else 2)
