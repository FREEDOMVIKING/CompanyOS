#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.finops import FinancialIntent, FinancialSafetyValidator, LiveActivationGate, FinOpsStatus

intent = FinancialIntent(
    chain="solana",
    amount=1,
    destination="TEST_DEST",
    purpose="verify"
).normalize()
assert intent["idempotency_key"]

validation = FinancialSafetyValidator().validate({
    "status":"dry_run_authorized",
    "idempotency_key":"x"
})
assert validation["passed"] is True

root = Path(tempfile.mkdtemp())
activation = LiveActivationGate(root).evaluate(
    {
        "adapter_present":True,
        "signer_command_configured":True,
        "solana_rpc_configured":True,
        "evm_rpc_configured":False,
        "bitcoin_rpc_configured":False,
    },
    {"passed":True}
)
assert activation["eligible_for_manual_live_enable"] is True
assert activation["live_execution_currently_enabled"] is False

assert FinOpsStatus().status()["status"] == "phase26000_autonomous_financial_safety_validation_ready"

print(json.dumps({
    "success":True,
    "status":"phase25001_26000_verification_passed",
    "cycle_status":"phase26000_autonomous_financial_safety_validation_ready",
    "live_execution_automatic_enable":False
}, indent=2))
