#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.operations import *

root=Path(tempfile.mkdtemp())

g=PersistentGoalTracker(root).upsert("g1","grow",1,.5)
assert g["status"]=="active"
assert BackgroundJobScheduler().build(["daily"],["weekly"],[]) 
assert CrossDepartmentCoordinator().coordinate([{"department":"sales","handoffs":[{"to":"finance"}]}])["handoffs"]
assert "improve_retention" in ContinuousBusinessOptimizer().recommend({"retention_rate":.2})
assert PersistentFailureRecovery().plan([{"kind":"queue_stall"}])[0]["recovery_action"]=="restart_worker"
assert OperatingMetrics().score({"revenue_growth":.5,"retention_rate":.6,"gross_margin":.7,"conversion_rate":.1,"reliability":1,"customer_satisfaction":.8})["operating_score"]>0
assert OperatingPolicyEngine().evaluate([{"kind":"contract_signature"}])["approval_queue"]
assert RuntimeStatus().status()["status"]=="phase2600_persistent_autonomous_operations_ready"

print(json.dumps({
    "success":True,
    "status":"phase2301_2600_verification_passed",
    "cycle_status":"phase2600_persistent_autonomous_operations_ready"
},indent=2))
