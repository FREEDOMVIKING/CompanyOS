#!/usr/bin/env python3
from pathlib import Path
import argparse, os, uuid

def load_env():
    p=Path(".env")
    if not p.exists():
        raise SystemExit("ERROR: run from ~/companyos; .env missing")
    for line in p.read_text(errors="ignore").splitlines():
        line=line.strip()
        if line and not line.startswith("#") and "=" in line:
            k,v=line.split("=",1)
            os.environ[k.strip()] = v.strip().strip('"').strip("'")

load_env()

from companyos.walletintegration.autonomous_financial_bridge_factory import build_autonomous_financial_bridge
from companyos.walletintegration.autonomous_financial_execution_bridge import AutonomousFinancialAction

ap=argparse.ArgumentParser()
ap.add_argument("--destination", required=True)
ap.add_argument("--sol", type=float, required=True)
ap.add_argument("--action-id", default="")
ap.add_argument("--source", default="autonomous_ceo")
ap.add_argument("--live", action="store_true")
ap.add_argument("--confirm-token", default="")
args=ap.parse_args()

action=AutonomousFinancialAction(
    action_id=args.action_id or str(uuid.uuid4()),
    action_type="sol_transfer",
    destination=args.destination,
    amount_sol=args.sol,
    source=args.source,
    live_requested=bool(args.live),
    confirm_token=args.confirm_token,
)

r=build_autonomous_financial_bridge().execute(action)

print("=== AUTONOMOUS FINANCIAL EXECUTION BRIDGE ===")
print("ACTION ID:", r.action_id)
print("MODE:", r.mode)
print("ACCEPTED:", r.accepted)
print("REASON:", r.reason)
print("STATE:", r.state or "NONE")
print("SIGNATURE:", r.signature or "NONE")
print("CONFIRMATION:", r.confirmation_status or "NONE")
print("LIFECYCLE ID:", r.lifecycle_id or "NONE")

raise SystemExit(0 if r.accepted else 2)
