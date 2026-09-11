#!/usr/bin/env python3
from pathlib import Path
import uuid

from companyos.walletintegration.solana_signer_key_adapter import load_signer_material
from companyos.walletintegration.live_solana_execution_engine import LiveSolanaExecutionEngine
from companyos.walletintegration.production_execution_coordinator import (
    ProductionExecutionCoordinator,
    ProductionExecutionRequest,
)


def load_env():
    candidates = [
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        raise SystemExit("PHASE85_COORDINATOR_DRY_RUN: FAIL - env file not found")

    cfg = {}
    for line in p.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip("'\"")
    return p, cfg


env_path, cfg = load_env()
rpc = cfg.get("SOLANA_RPC_URL", "")
secret = cfg.get("SOLANA_PRIVATE_KEY", "")
enc = cfg.get("SOLANA_PRIVATE_KEY_ENCODING", "auto")
reserve = float(cfg.get("COMPANYOS_LIVE_MIN_RESERVE", "0") or 0)

material = load_signer_material(secret, enc)

engine = LiveSolanaExecutionEngine(
    rpc_url=rpc,
    secret=secret,
    encoding=enc,
    wallet_address=material.public_address,
    reserve_sol=reserve,
    broadcast_enabled=False,
)

coord = ProductionExecutionCoordinator(engine=engine)

key = "phase85-" + uuid.uuid4().hex

req = ProductionExecutionRequest(
    action_type="zero_lamport_self_transfer",
    amount_lamports=0,
    destination=material.public_address,
    allow_broadcast=False,
)

first = coord.execute(req, idempotency_key=key)
second = coord.execute(req, idempotency_key=key)

print("ENV_FILE:", env_path)
print("FIRST_ACCEPTED:", first.accepted)
print("FIRST_STATE:", first.state)
print("FIRST_REASON:", first.reason)
print("FIRST_SUCCESS:", first.success)
print("FIRST_BROADCAST_REQUESTED: False")
print("SECOND_ACCEPTED:", second.accepted)
print("SECOND_REASON:", second.reason)
print("DUPLICATE_BLOCKED:", second.reason == "duplicate_idempotency_key")
print("PRIVATE_KEY_PRINTED: False")
print("TRANSACTION_BROADCAST: False")

passed = (
    first.accepted
    and first.state == "SIGNED"
    and first.reason == "signed_not_broadcast"
    and second.accepted is False
    and second.reason == "duplicate_idempotency_key"
)

print("PHASE85_COORDINATOR_DRY_RUN:", "PASS" if passed else "FAIL")
raise SystemExit(0 if passed else 1)
