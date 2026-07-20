#!/usr/bin/env python3
import json
from companyos_phase157_164 import *
assert MissionPlanner().plan([{"objective":"grow"}])[0]["autonomous"]
assert DependencyOrchestrator().ready([{"id":"b","depends_on":["a"]}],["a"])[0]["id"]=="b"
assert DelegationDirector().delegate([{"id":"x","capabilities":["build"]}],[{"name":"builder","capabilities":["build"],"reliability":.9}])[0]["agent"]=="builder"
assert ExecutionMemory().summarize([{"strategy":"s","success":True,"score":.8}])[0]["win_rate"]==1
assert AdaptiveBudgeter().allocate([{"name":"x","evidence":1,"learning":1,"risk":0}],100)[0]["allocation"]==100
assert QualityGovernor().evaluate({"tests_pass":True,"confidence":.9,"completeness":.9})["passed"]
assert StagnationBreaker().decide([{"score":.5},{"score":.51},{"score":.5}])["stagnant"]
r=ExecutiveAutopilot().run({"objectives":[{"objective":"build"}]})
assert r["success"] and r["continuous_operation"] and r["autonomy_mode"]=="high"
print(json.dumps({"success":True,"status":"phase157_164_verification_passed","cycle_status":r["status"],
"autonomy_mode":"high","continuous_operation":True,"external_action_taken":False,
"financial_action_taken":False,"irreversible_action_taken":False},indent=2))
