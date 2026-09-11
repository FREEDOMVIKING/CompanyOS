#!/usr/bin/env python3

from companyos.walletintegration.boot_orchestrator import CompanyOSBootOrchestrator

result = CompanyOSBootOrchestrator().run()

print("READY:", result.ready)
print("REASON:", result.reason)
print("ENV_FILE:", result.env_file)
print("RPC_CONFIGURED:", result.rpc_configured)
print("KEY_CONFIGURED:", result.key_configured)
print("WALLET_DERIVED:", result.wallet_derived)
print("WALLET_ADDRESS:", result.wallet_address)
print("LIVE_BALANCE_OK:", result.live_balance_ok)
print("LIVE_BALANCE_SOL:", result.live_balance_sol)
print("STARTUP_RECONCILIATION_OK:", result.startup_reconciliation_ok)
print("UNRESOLVED_RECORDS:", result.unresolved_records)
print("SIGNED_PENDING_RECORDS:", result.signed_pending_records)
print("PRIVATE_KEY_PRINTED:", result.private_key_printed)
print("BROADCAST_ATTEMPTED:", result.broadcast_attempted)
print("PHASE88_BOOT_READINESS:", "PASS" if result.ready else "BLOCKED")

raise SystemExit(0 if result.ready else 2)
