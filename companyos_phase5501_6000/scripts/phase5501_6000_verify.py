#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.orchestration import *

root=Path(tempfile.mkdtemp())
g=PersistentGoalGraph(root)
g.upsert_goal("g1","grow",.9)
assert g.load()["goals"]["g1"]["objective"]=="grow"

registry=CapabilityRegistry().build([{"name":"research","capabilities":["research"],"health":1,"capacity":1}])
assert "research" in registry

spawned=DynamicAgentFactory().fill_gaps(["build"],registry)
assert spawned and spawned[0]["role"]=="build_specialist"

ranked=PriorityArbitrator().rank([{"id":"a","impact":1,"urgency":1,"confidence":1,"effort":1,"risk":0}])
assert ranked[0]["priority_score"]>0

health=UnifiedSystemHealth().evaluate([{"name":"x","healthy":True,"consecutive_failures":0,"backlog":0}])
assert health["healthy"] is True

assert AuthorityRouter().route([{"kind":"contract_signature"}])["approval_queue"]
assert OrchestrationStatus().status()["status"]=="phase6000_unified_autonomous_orchestration_brain_ready"

print(json.dumps({
    "success":True,
    "status":"phase5501_6000_verification_passed",
    "cycle_status":"phase6000_unified_autonomous_orchestration_brain_ready"
},indent=2))
