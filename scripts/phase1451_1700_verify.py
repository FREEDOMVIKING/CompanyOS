#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.organization import *

root=Path(tempfile.mkdtemp())
assert GoalDecomposer().decompose("grow company")
assert PlanningHorizons().build(GoalDecomposer().decompose("x"))["daily"] is not None
assert PriorityEngine().rank([{"impact":1,"urgency":1,"confidence":1,"risk":0,"effort":1}])[0]["priority_score"]>0
reg=AgentRegistry(root)
a=reg.create("research_specialist",["research"])
assert a["status"]=="active"
assert DynamicStaffingManager().evaluate({"research":2},reg)
perf=AgentPerformanceManager().evaluate([{"quality":.9,"speed":.8,"reliability":.9,"learning":.8}])
assert perf[0]["performance_score"]>.8
assert BudgetArbitrator().allocate([{"department":"growth","expected_value":.8,"confidence":.8,"urgency":.8,"requested":200}],500)["allocations"]
assert ResourceConflictResolver().resolve([{"resource":"builder","department":"product","priority":.9},{"resource":"builder","department":"growth","priority":.5}])[0]["winner"]=="product"
assert ApprovalRouter().route([{"kind":"bank_transfer","amount":1000}])["approval_queue"]
assert RuntimeStatus().status()["status"]=="phase1700_self_managing_ai_organization_ready"
print(json.dumps({"success":True,"status":"phase1451_1700_verification_passed","cycle_status":"phase1700_self_managing_ai_organization_ready"},indent=2))
