#!/usr/bin/env python3
import json
from companyos.solanasim import SolanaSimulationPlan, SolanaSimulationGate, SolanaSimulationStatus

p = SolanaSimulationPlan().build("A","B",1,"BH")
assert p["success"] is True
assert p["plan"]["broadcast"] is False

g = SolanaSimulationGate().evaluate(
    rpc_ok=True,
    identity_ok=True,
    balance_ok=True,
    simulation_result={"success":True,"result":{"value":{"err":None}}}
)
assert g["simulation_passed"] is True
assert g["ready_for_live_review"] is True
assert g["ready_for_live"] is False

s = SolanaSimulationStatus().status()
assert s["broadcast_attempted"] is False
assert s["live_execution_auto_enabled"] is False

print(json.dumps({
    "success":True,
    "status":"phase48001_50000_verification_passed",
    "cycle_status":"phase50000_solana_nonbroadcast_simulation_ready"
}, indent=2))
