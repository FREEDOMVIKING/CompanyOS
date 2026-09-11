#!/usr/bin/env python3
import json
from companyos.capabilityops import StageCapabilityRouter, ControlledAutonomyPolicy, RealCapabilityOperatingExecutor, CapabilityOpsStatus

router = StageCapabilityRouter()
assert router.resolve("research", {"research"})["matched"] is True

policy = ControlledAutonomyPolicy()
assert policy.decide({"impact":"low","reversible":True})["decision"] == "autonomous_allowed"
assert policy.decide({"changes_credentials":True})["decision"] == "approval_required"
assert policy.decide({"moves_money":True,"within_treasury_policy":False})["decision"] == "blocked"
assert policy.decide({"reversible":False})["decision"] == "approval_required"

rows = RealCapabilityOperatingExecutor(router, policy).build_stage_plan(
    ["research","budget","launch_review"],
    {"research","finance","release"},
    treasury_policy_satisfied=True
)
assert rows[0]["execution_state"] == "ready_to_execute_real_capability"
assert rows[1]["execution_state"] == "ready_to_execute_real_capability"
assert rows[2]["execution_state"] == "approval_required"

assert CapabilityOpsStatus().status()["status"] == "phase32000_real_capability_wiring_ready"

print(json.dumps({
    "success": True,
    "status": "phase30001_32000_verification_passed",
    "cycle_status": "phase32000_real_capability_wiring_ready"
}, indent=2))
