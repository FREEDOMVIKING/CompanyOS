#!/usr/bin/env python3

from companyos.walletintegration.production_runtime_supervisor import ProductionRuntimeSupervisor

sup = ProductionRuntimeSupervisor(interval_seconds=15, max_consecutive_failures=3)
state, feed, gate = sup.startup()
state = sup.cycle(state, feed, gate)

print("RUNNING:", state.running)
print("READY:", state.ready)
print("REASON:", state.reason)
print("CYCLE_COUNT:", state.cycle_count)
print("RPC_OK:", state.rpc_ok)
print("STALE:", state.stale)
print("WALLET_ADDRESS:", state.wallet_address)
print("SOL_BALANCE:", state.sol_balance)
print("SPENDABLE_SOL:", state.spendable_sol)
print("UNRESOLVED_RECORDS:", state.unresolved_records)
print("SIGNED_PENDING_RECORDS:", state.signed_pending_records)
print("CONSECUTIVE_FAILURES:", state.consecutive_failures)
print("BROADCAST_ATTEMPTED:", state.broadcast_attempted)
print("PRIVATE_KEY_PRINTED:", state.private_key_printed)

passed = (
    state.running
    and state.ready
    and state.rpc_ok
    and not state.stale
    and state.unresolved_records == 0
    and state.broadcast_attempted is False
)

print("PHASE89_SUPERVISOR_ONCE:", "PASS" if passed else "FAIL")
raise SystemExit(0 if passed else 1)
