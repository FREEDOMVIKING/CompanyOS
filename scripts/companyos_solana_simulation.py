#!/usr/bin/env python3
import json, os, shlex, subprocess
from pathlib import Path
from companyos.solanasim import SolanaIdentityProvider, SolanaRpcClient, SolanaSimulationPlan, SolanaSimulationGate

root = Path.home()/"companyos"
identity = SolanaIdentityProvider(root).get()
rpc = SolanaRpcClient()

blockhash = rpc.latest_blockhash()
address = identity.get("public_address") if identity.get("success") else None
balance = rpc.balance(address) if address else {"success":False,"status":"identity_missing"}

balance_lamports = None
if balance.get("success"):
    balance_lamports = (balance.get("result") or {}).get("value")

plan = None
if identity.get("success") and blockhash.get("success"):
    bh = ((blockhash.get("result") or {}).get("value") or {}).get("blockhash")
    plan = SolanaSimulationPlan().build(
        identity["public_address"],
        identity["public_address"],
        0,
        bh
    )

simulation_result = None
signer_cmd = os.getenv("MULTICHAIN_SIGNER_COMMAND","").strip()

# Optional signer-assisted non-broadcast validation.
# We only simulate when the signer returns a serialized signed transaction.
if signer_cmd and plan:
    payload = {
        "action":"sign_spl_transfer",
        "source":identity["public_address"],
        "destination":identity["public_address"],
        "mint":"So11111111111111111111111111111111111111112",
        "amount":0,
        "recent_blockhash":plan["plan"]["recent_blockhash"],
        "commitment":"confirmed",
        "maxRetries":0,
        "dry_run":True,
        "broadcast":False
    }
    try:
        proc = subprocess.run(
            shlex.split(signer_cmd),
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=30
        )
        parsed = None
        if proc.stdout.strip():
            try:
                parsed = json.loads(proc.stdout.strip().splitlines()[-1])
            except Exception:
                parsed = None
        tx_b64 = parsed.get("signed_transaction_base64") if isinstance(parsed,dict) else None
        if tx_b64:
            simulation_result = rpc.simulate(tx_b64)
        else:
            simulation_result = {
                "success":False,
                "status":"signer_did_not_return_serialized_transaction",
                "returncode":proc.returncode
            }
    except Exception as exc:
        simulation_result = {
            "success":False,
            "status":"signer_validation_exception",
            "error":type(exc).__name__,
            "message":str(exc)
        }

gate = SolanaSimulationGate().evaluate(
    rpc_ok=blockhash.get("success"),
    identity_ok=identity.get("success"),
    balance_ok=balance.get("success"),
    simulation_result=simulation_result
)

print(json.dumps({
    "success":True,
    "status":"solana_nonbroadcast_simulation_check_complete",
    "identity":identity,
    "latest_blockhash":blockhash,
    "balance_lamports":balance_lamports,
    "plan":plan,
    "simulation":simulation_result,
    "gate":gate
}, indent=2))
