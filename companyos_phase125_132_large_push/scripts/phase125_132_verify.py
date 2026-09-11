#!/usr/bin/env python3
import json
from companyos_phase125_132 import *

assert AuthorityModel().evaluate({"type":"internal_code_change"})["allowed"] is True
assert AuthorityModel().evaluate({"type":"transfer_funds"})["allowed"] is False
assert AuthorityModel().evaluate({"type":"transfer_funds","explicit_approval":True})["allowed"] is True

tasks = AutonomyScheduler().select([
    {"id":"a","status":"queued","value":.9,"urgency":.8,"learning_value":.9,"risk":.1},
    {"id":"b","status":"queued","approval_required":True,"approved":False,"value":1.0},
])
assert [x["id"] for x in tasks] == ["a"]

assert BuilderLoop().next_action({"build_exists":False})["autonomous"] is True
assert SelfRepairEngine().plan({"kind":"test_failure","attempts":0})["autonomous"] is True
assert ExperimentBudget().authorize(10,100,.1)["allowed"] is True
assert ExperimentBudget().authorize(1000,100,.1)["allowed"] is False
assert LaunchController().evaluate({"scope":"local","reversible":True,"bounded":True})["autonomous_launch_allowed"] is True
assert LaunchController().evaluate({"scope":"public","reversible":False,"bounded":False})["approval_required"] is True

portfolio = PortfolioAutopilot().review([
    {"name":"good","traction":.9,"margin":.8,"learning":.8,"risk":.1}
])
assert portfolio[0]["autonomous_action"] == "continue_and_scale_internal_capacity"

cycle = AutonomousCompanyLoop().run({
    "tasks":[{"id":"t1","status":"queued","value":.9,"urgency":.8,"learning_value":.8,"risk":.1}],
    "build_state":{"build_exists":True,"tests_pass":False,"validated":False},
    "fault":{"kind":"test_failure","attempts":1},
    "requested_cost":10,
    "remaining_budget":100,
    "experiment_risk":.1,
    "launch":{"scope":"local","reversible":True,"bounded":True},
    "ventures":[{"name":"v","traction":.8,"margin":.8,"learning":.7,"risk":.2}],
    "actions":[{"type":"internal_code_change"}],
})
assert cycle["success"] is True
assert cycle["autonomy_mode"] == "high"
assert cycle["external_action_taken"] is False
assert cycle["financial_action_taken"] is False
assert cycle["irreversible_action_taken"] is False

print(json.dumps({
    "success": True,
    "status": "phase125_132_verification_passed",
    "cycle_status": cycle["status"],
    "autonomy_mode": cycle["autonomy_mode"],
    "external_action_taken": cycle["external_action_taken"],
    "financial_action_taken": cycle["financial_action_taken"],
    "irreversible_action_taken": cycle["irreversible_action_taken"],
}, indent=2))
