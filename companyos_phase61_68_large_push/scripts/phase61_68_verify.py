#!/usr/bin/env python3
import json
from companyos_phase61_68 import (
    ObjectiveManager, TaskGraph, ResourcePlanner, ExperimentEngine,
    MarketFeedbackEngine, DelegationEngine, GovernanceEngine, ExecutiveLoop,
)

assert ObjectiveManager().prioritize([
    {"name":"a","impact":10,"urgency":10,"confidence":1,"effort":1},
    {"name":"b","impact":2,"urgency":2,"confidence":.5,"effort":5},
])[0]["name"] == "a"

graph = TaskGraph().order([
    {"id":"1","depends_on":[]},
    {"id":"2","depends_on":["1"]},
])
assert graph["success"] is True
assert [x["id"] for x in graph["ordered"]] == ["1","2"]

alloc = ResourcePlanner().allocate([
    {"id":"a","value":10,"cost":2},
    {"id":"b","value":1,"cost":10},
], 3)
assert alloc["chosen"][0]["id"] == "a"

exp = ExperimentEngine().design("x","conversion",1,2,100)
assert ExperimentEngine().evaluate(exp, 2.5)["success"] is True

fb = MarketFeedbackEngine().summarize([
    {"sentiment":1,"demand":.8,"theme":"speed"},
    {"sentiment":.5,"demand":.6,"theme":"price"},
])
assert fb["count"] == 2

delegated = DelegationEngine().assign(
    [{"id":"t1","required_capabilities":["research"]}],
    [{"name":"research_agent","capabilities":["research","evidence_analysis"]}]
)
assert delegated[0]["assigned_agent"] == "research_agent"

gov = GovernanceEngine()
assert gov.classify({"external":True,"financial":True,"irreversible":True})["allowed"] is False
assert gov.classify({"external":True,"financial":True,"irreversible":True,"explicit_approval":True})["allowed"] is True

cycle = ExecutiveLoop().run({
    "objectives":[{"name":"validate offer","impact":10,"urgency":8,"confidence":.8,"effort":2}],
    "tasks":[
        {"id":"r1","title":"research","depends_on":[],"value":10,"cost":2,"required_capabilities":["research"]},
        {"id":"s1","title":"strategy","depends_on":["r1"],"value":8,"cost":2,"required_capabilities":["strategy"]},
    ],
    "capacity":5,
    "agents":[
        {"name":"research_agent","capabilities":["research"]},
        {"name":"strategy_agent","capabilities":["strategy"]},
    ],
    "actions":[{"type":"internal_plan","external":False}],
})
assert cycle["success"] is True
assert cycle["external_action_taken"] is False

print(json.dumps({
    "success": True,
    "status": "phase61_68_verification_passed",
    "cycle_status": cycle["status"],
    "delegated_count": len(cycle["delegated_tasks"]),
    "external_action_taken": cycle["external_action_taken"],
}, indent=2))
