#!/usr/bin/env python3
from pathlib import Path

from companyos.walletintegration.solana_rpc_preflight import rpc_call
from companyos.walletintegration.solana_legacy_tx_builder import build_zero_lamport_self_transfer
from companyos.walletintegration.solana_transaction_simulator import simulate_signed_transaction


def load_env():
    candidates = [
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        raise SystemExit("PHASE79_SIMULATION_TEST: FAIL - env file not found")

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

if not rpc or not secret:
    raise SystemExit("PHASE79_SIMULATION_TEST: FAIL - RPC or key missing")

latest = rpc_call(rpc, "getLatestBlockhash", [{"commitment": "confirmed"}])
blockhash = ((latest.get("result") or {}).get("value") or {}).get("blockhash")
if not blockhash:
    raise SystemExit("PHASE79_SIMULATION_TEST: FAIL - blockhash unavailable")

tx = build_zero_lamport_self_transfer(secret, enc, blockhash)

sim = simulate_signed_transaction(rpc, tx.transaction_base64)

print("ENV_FILE:", env_path)
print("WALLET_ADDRESS:", tx.wallet_address)
print("DESTINATION:", tx.destination)
print("LAMPORTS:", tx.lamports)
print("TRANSACTION_SIGNED:", tx.signature_verified)
print("SIMULATE_TRANSACTION_CALLED: True")
print("RPC_OK:", sim.rpc_ok)
print("SIMULATION_OK:", sim.simulation_ok)
print("SIMULATION_ERR:", sim.err)
print("UNITS_CONSUMED:", sim.units_consumed)
print("LOG_COUNT:", len(sim.logs))

# Show only a few logs; these contain no private key.
for i, line in enumerate(sim.logs[:8], 1):
    print(f"LOG_{i}:", line)

print("PRIVATE_KEY_PRINTED: False")
print("SEND_TRANSACTION_CALLED: False")
print("TRANSACTION_BROADCAST: False")
print("FUNDS_MOVED: False")

passed = (
    tx.signature_verified
    and tx.lamports == 0
    and tx.destination == tx.wallet_address
    and sim.rpc_ok
    and sim.simulation_ok
)

print("PHASE79_SIMULATION_TEST:", "PASS" if passed else "FAIL")
raise SystemExit(0 if passed else 1)
