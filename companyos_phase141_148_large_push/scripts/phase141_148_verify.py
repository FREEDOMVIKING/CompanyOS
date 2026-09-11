#!/usr/bin/env python3
import json
from companyos_phase141_148 import *

missions = AutonomousResearcher().create_missions(
    [{"required_topics":["pricing","market"]}],
    [{"topic":"market"}],
)
assert len(missions) == 1
assert missions[0]["topic"] == "pricing"

offers = RevenueOperator().evaluate([
    {"name":"a","price":100,"expected_customers":10,"variable_cost":20,"conversion":.5}
])
assert offers[0]["funds_moved"] is False

channels = CustomerAcquisitionEngine().rank_channels([
    {"name":"content","reach":.8,"intent":.7,"cost_efficiency":.9,"speed":.5,"reversible":True,"bounded":True}
])
assert channels[0]["test_autonomously"] is True

ops = OperationsAutopilot().decide([
    {"id":"i1","proposed_action":"restart_worker"}
])
assert ops[0]["autonomous_action_allowed"] is True

assert CodeEvolutionEngine().authorize({"scope":"bug_fix","reversible":True})["autonomous_change_allowed"] is True
assert CodeEvolutionEngine().authorize({"scope":"unknown","reversible":False})["approval_required"] is True

reps = VentureReplicator().candidates([
    {"name":"v1","traction":.8,"repeatability":.8,"margin":.7}
])
assert reps[0]["replication_allowed"] is True

reb = ResourceRebalancer().rebalance([
    {"name":"v1","traction":.8,"learning":.7,"margin":.7,"risk":.2}
], 100)
assert reb["autonomous_internal_rebalance"] is True
assert round(reb["allocations"][0]["capacity"], 4) == 100.0

cycle = SelfDirectedEnterprise().run({
    "goals":[{"required_topics":["customer_pain"]}],
    "evidence":[],
    "offers":[{"name":"offer","price":50,"expected_customers":20,"variable_cost":10,"conversion":.4}],
    "channels":[{"name":"organic","reach":.8,"intent":.8,"cost_efficiency":.9,"speed":.6}],
    "incidents":[{"proposed_action":"run_healthcheck"}],
    "code_change":{"scope":"internal_module","reversible":True},
    "ventures":[{"name":"v","traction":.8,"repeatability":.8,"margin":.7,"learning":.8,"risk":.2}],
    "total_capacity":100,
})
assert cycle["success"] is True
assert cycle["autonomy_mode"] == "high"
assert cycle["external_action_taken"] is False
assert cycle["financial_action_taken"] is False
assert cycle["irreversible_action_taken"] is False

print(json.dumps({
    "success": True,
    "status": "phase141_148_verification_passed",
    "cycle_status": cycle["status"],
    "autonomy_mode": cycle["autonomy_mode"],
    "external_action_taken": cycle["external_action_taken"],
    "financial_action_taken": cycle["financial_action_taken"],
    "irreversible_action_taken": cycle["irreversible_action_taken"],
}, indent=2))
