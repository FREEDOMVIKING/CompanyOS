#!/usr/bin/env python3
from pathlib import Path
import argparse
import sys

# Bootstrap project imports before importing CompanyOS modules.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from companyos.runtime_bootstrap import load_dotenv
load_dotenv(ROOT)

from companyos.walletintegration.autonomous_financial_runtime_adapter import (
    execute_runtime_financial_intent,
)

ap = argparse.ArgumentParser(description="CompanyOS autonomous finance runtime CLI")
ap.add_argument("--destination", required=True)
ap.add_argument("--sol", required=True, type=float)
ap.add_argument("--action-id", default="")
ap.add_argument("--source", default="autonomous_runtime")
ap.add_argument("--live", action="store_true")
ap.add_argument("--confirm-token", default="")
args = ap.parse_args()

result = execute_runtime_financial_intent(
    destination=args.destination,
    amount_sol=args.sol,
    action_id=args.action_id,
    source=args.source,
    requested_mode="live" if args.live else "dry_run",
    confirm_token=args.confirm_token,
)

print("=== COMPANYOS RUNTIME FINANCIAL INTENT ===")
print("MODE:", result.mode)
print("ACTION ID:", result.action_id)
print("ACCEPTED:", result.accepted)
print("REASON:", result.reason)
print("STATE:", result.state or "NONE")
print("SIGNATURE:", result.signature or "NONE")
print("CONFIRMATION:", result.confirmation_status or "NONE")
print("LIFECYCLE ID:", result.lifecycle_id or "NONE")

raise SystemExit(0 if result.accepted else 2)
