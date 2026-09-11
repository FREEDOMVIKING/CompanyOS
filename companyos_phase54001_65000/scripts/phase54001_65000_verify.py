#!/usr/bin/env python3
import json, os
from companyos.liveintegration import LiveExecutionPolicy, ReceiptReconciler, FinalLiveIntegrationStatus

os.environ["COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION"]="false"
os.environ["COMPANYOS_LIVE_MAX_SINGLE"]="0.001"
p=LiveExecutionPolicy()
assert p.enabled is False
assert p.check_amount(0.0005)["allowed"] is True
assert p.check_amount(0.01)["allowed"] is False

r=ReceiptReconciler().reconcile(
    {"success":True,"signature":"abc"},
    {"success":True,"status":"confirmed"}
)
assert r["success"] is True

s=FinalLiveIntegrationStatus().status()
assert s["autonomous_unbounded_spending"] is False
assert s["live_execution_requires_explicit_env_enable"] is True

print(json.dumps({
    "success":True,
    "status":"phase54001_65000_verification_passed",
    "cycle_status":"phase65000_final_live_financial_integration_ready"
}, indent=2))
