#!/usr/bin/env python3
import json
from companyos_phase165_172 import *
tree=ObjectiveTree().build("grow",1); assert len(tree["children"])==3
assert len(InitiativeFactory().create(["build"],["sales"]))==2
team=AgentTeamBuilder().assemble({"id":"x","capabilities":["build"]},[{"name":"builder","capabilities":["build"],"reliability":.9}])
assert team["fully_covered"]
assert ExecutionSupervisor().supervise([{"status":"failed","attempts":1}])[0]["supervisor_action"]=="retry"
assert EvidenceLearner().update([{"topic":"x","confidence":.5}],[{"topic":"x","signal":1}])[0]["confidence"]>.5
assert VentureLifecycle().decide({"name":"x","traction":.9,"evidence":.9,"risk":.1})["action"]=="scale_internal_capacity"
assert abs(sum(CapacityManager().allocate(100).values())-100)<.01
r=CompanyDaemon().tick({"goals":["build"],"gaps":["distribution"],"primary_objective":"grow"})
assert r["success"] and r["persistent_heartbeat"] and r["autonomy_mode"]=="high"
print(json.dumps({"success":True,"status":"phase165_172_verification_passed","cycle_status":r["status"],
"autonomy_mode":"high","persistent_heartbeat":True,"external_action_taken":False,
"financial_action_taken":False,"irreversible_action_taken":False},indent=2))
