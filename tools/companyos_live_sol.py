#!/usr/bin/env python3
from pathlib import Path
import argparse
import os
import uuid

def load_env():
    p = Path(".env")
    if not p.exists():
        raise SystemExit("ERROR: .env not found; run from ~/companyos")
    for line in p.read_text(errors="ignore").splitlines():
        line=line.strip()
        if line and not line.startswith("#") and "=" in line:
            k,v=line.split("=",1)
            os.environ[k.strip()] = v.strip().strip('"').strip("'")

load_env()

from companyos.walletintegration.solana_signer_key_adapter import load_signer_material
from companyos.walletintegration.live_solana_execution_engine import LiveSolanaExecutionEngine
from companyos.walletintegration.production_execution_coordinator import ProductionExecutionCoordinator
from companyos.walletintegration.execution_policy import ExecutionPolicy, ExecutionAuditLedger
from companyos.walletintegration.controlled_production_sol_gateway import ControlledProductionSolGateway
from companyos.walletintegration.live_execution_control import LiveExecutionControl

ap = argparse.ArgumentParser(description="CompanyOS live SOL execution controller")
ap.add_argument("--destination", required=True)
ap.add_argument("--sol", required=True, type=float)
ap.add_argument("--live", action="store_true")
ap.add_argument("--confirm-token", default="")
ap.add_argument("--idempotency-key", default="")
ap.add_argument("--source", default="manual")
args = ap.parse_args()

if args.sol <= 0:
    raise SystemExit("ERROR: --sol must be > 0")

material = load_signer_material(
    os.environ["SOLANA_PRIVATE_KEY"],
    os.getenv("SOLANA_PRIVATE_KEY_ENCODING", "auto"),
)

required_live_token = os.getenv("COMPANYOS_LIVE_CONFIRM_TOKEN", "")
control = LiveExecutionControl(required_token=required_live_token)
auth = control.authorize(
    live_requested=bool(args.live),
    provided_token=args.confirm_token,
    source=args.source,
    metadata={"destination": args.destination, "amount_sol": args.sol},
)

print("=== LIVE EXECUTION CONTROL ===")
print("LIVE REQUESTED:", bool(args.live))
print("AUTHORIZED:", auth.allowed)
print("REASON:", auth.reason)

if not auth.allowed:
    raise SystemExit(3)

single_cap = float(os.getenv("COMPANYOS_SOL_SINGLE_CAP_SOL", "150"))
daily_cap = float(os.getenv("COMPANYOS_SOL_DAILY_CAP_SOL", "200"))
minimum = float(os.getenv("COMPANYOS_SOL_MIN_TRANSFER_SOL", "0.000001"))
reserve = float(os.getenv("COMPANYOS_SOL_RESERVE_SOL", "0.01"))
require_allowlist = os.getenv("COMPANYOS_SOL_REQUIRE_ALLOWLIST", "false").lower() == "true"
allow_self = os.getenv("COMPANYOS_SOL_ALLOW_SELF_TRANSFER", "true").lower() == "true"

engine = LiveSolanaExecutionEngine(
    rpc_url=os.environ["SOLANA_RPC_URL"],
    secret=os.environ["SOLANA_PRIVATE_KEY"],
    encoding=os.getenv("SOLANA_PRIVATE_KEY_ENCODING", "auto"),
    wallet_address=material.public_address,
    reserve_sol=reserve,
    broadcast_enabled=bool(args.live),
)

coordinator = ProductionExecutionCoordinator(engine=engine)
ledger = ExecutionAuditLedger()
policy = ExecutionPolicy(
    daily_cap_sol=daily_cap,
    single_cap_sol=single_cap,
    minimum_transfer_sol=minimum,
    reserve_sol=reserve,
    require_destination_allowlist=require_allowlist,
    allow_self_transfer=allow_self,
)

gateway = ControlledProductionSolGateway(
    coordinator=coordinator,
    wallet_address=material.public_address,
    policy=policy,
    ledger=ledger,
    allowlist_path=Path("config/solana_destination_allowlist.json"),
)

lamports = int(round(args.sol * 1_000_000_000))
result = gateway.execute(
    destination=args.destination,
    amount_lamports=lamports,
    allow_broadcast=bool(args.live),
    confirm_token=args.confirm_token if args.live else "",
    idempotency_key=args.idempotency_key or f"live-control-{uuid.uuid4()}",
    source=args.source,
)

print()
print("=== EXECUTION RESULT ===")
print("MODE:", "LIVE" if args.live else "DRY RUN")
print("ACCEPTED:", result.accepted)
print("REASON:", result.reason)
print("STATE:", result.state or "NONE")
print("SIGNATURE:", result.signature or "NONE")
print("CONFIRMATION:", result.confirmation_status or "NONE")
print("LIFECYCLE ID:", result.lifecycle_id or "NONE")

raise SystemExit(0 if result.accepted else 2)
