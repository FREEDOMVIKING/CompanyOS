#!/usr/bin/env python3
import json
from companyos_phase133_140 import *

ops = OpportunityHunter().discover([
    {"name":"good","demand":.9,"urgency":.8,"willingness_to_pay":.9,"competition":.2,"confidence":.8},
    {"name":"weak","demand":.2,"urgency":.2,"willingness_to_pay":.2,"competition":.9,"confidence":.3},
])
assert ops[0]["name"] == "good"

bp = VentureDesigner().design({"name":"AI workflow service"})
assert bp["status"] == "blueprint_ready"

plan = BusinessBuilder().plan(bp)
assert len(plan) >= 5
assert all(x["autonomous"] for x in plan)

batch = ContinuousExecutor().next_batch([
    {"id":"a","status":"queued","priority":.9,"value":.9,"learning_value":.8,"risk":.1},
    {"id":"b","status":"queued","approval_required":True,"approved":False,"priority":1},
])
assert [x["id"] for x in batch] == ["a"]

assert SelfOptimizer().evaluate({"kind":"task_routing","reversible":True,"bounded":True})["auto_apply"] is True
assert SelfOptimizer().evaluate({"kind":"unknown","reversible":False})["approval_required"] is True

assigned = AgentMesh().assign(
    [{"id":"t","required_capabilities":["research"]}],
    [{"name":"research_agent","capabilities":["research"],"reliability":.9,"load":.1}]
)
assert assigned[0]["assigned_agent"] == "research_agent"

exp = PortfolioExpander().decide([
    {"name":"v1","status":"active","traction":.8,"margin":.7,"learning":.8}
], max_active=5)
assert exp["autonomous_expansion_allowed"] is True

cycle = AutonomousBusinessEngine().run({
    "signals":[{"name":"AI microservice","demand":.9,"urgency":.8,"willingness_to_pay":.85,"competition":.3,"confidence":.8}],
    "agents":[{"name":"builder_agent","capabilities":["build"],"reliability":.9,"load":.2}],
    "optimization":{"kind":"task_routing","reversible":True,"bounded":True},
    "ventures":[{"name":"existing","status":"active","traction":.8,"margin":.7,"learning":.8}],
})
assert cycle["success"] is True
assert cycle["autonomy_mode"] == "high"
assert cycle["external_action_taken"] is False
assert cycle["financial_action_taken"] is False
assert cycle["irreversible_action_taken"] is False

print(json.dumps({
    "success": True,
    "status": "phase133_140_verification_passed",
    "cycle_status": cycle["status"],
    "autonomy_mode": cycle["autonomy_mode"],
    "external_action_taken": cycle["external_action_taken"],
    "financial_action_taken": cycle["financial_action_taken"],
    "irreversible_action_taken": cycle["irreversible_action_taken"],
}, indent=2))
