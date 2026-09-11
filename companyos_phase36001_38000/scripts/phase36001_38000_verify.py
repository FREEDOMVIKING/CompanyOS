#!/usr/bin/env python3
import json
from companyos.runtimeintegration import RuntimeRecoveryManager, RuntimeIntegrationStatus

mgr = RuntimeRecoveryManager()

assert mgr.classify_cycle({
    "results":[{"success":False,"status":"capability_missing"}]
})["next_action"] == "discover_or_build_missing_capabilities"

assert mgr.classify_cycle({
    "results":[{"success":False,"status":"approval_required"}]
})["next_action"] == "wait_for_approval_then_resume"

assert mgr.classify_cycle({
    "results":[{"success":True,"status":"verified_execution_complete"}]
})["next_action"] == "continue_next_cycle"

s = RuntimeIntegrationStatus().status()
assert s["status"] == "phase38000_integrated_autonomous_runtime_ready"
assert s["false_completion_prevention"] is True
assert s["live_money_auto_enable"] is False

print(json.dumps({
    "success":True,
    "status":"phase36001_38000_verification_passed",
    "cycle_status":"phase38000_integrated_autonomous_runtime_ready"
}, indent=2))
