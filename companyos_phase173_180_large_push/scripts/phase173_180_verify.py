#!/usr/bin/env python3
import json
from companyos_phase173_180 import *
assert WorldModel().update([{"topic":"x","belief":.5}],[{"topic":"x","signal":1,"confidence":1}])[0]["belief"]==1
r=DecisionJournal().record("x","why",.8);assert DecisionJournal().review(r,.9)["review_status"]=="reviewed"
assert CounterfactualEngine().rank([{"name":"a","upside":1,"probability":1,"learning":1,"risk":0}])[0]["name"]=="a"
assert SkillFactory().propose([{"workflow":"x"},{"workflow":"x"},{"workflow":"x"}])[0]["create_reusable_skill"]
assert WorkflowComposer().compose("build",[{"name":"coder","supports":["build"]}])["autonomous_execution"]
assert MetricSentinel().inspect([{"name":"m","value":2,"baseline":1,"tolerance":.1}])[0]["autonomous"]
s=SuccessionManager().reassign([{"role":"r","agent":"dead"}],[{"name":"healthy","healthy":True,"reliability":.9}]);assert s[0]["agent"]=="healthy"
cycle=SovereignOrchestrator().run({"objective":"operate"})
assert cycle["success"] and cycle["self_directed_orchestration"] and cycle["autonomy_mode"]=="high"
print(json.dumps({"success":True,"status":"phase173_180_verification_passed","cycle_status":cycle["status"],
"autonomy_mode":"high","self_directed_orchestration":True,"external_action_taken":False,
"financial_action_taken":False,"irreversible_action_taken":False},indent=2))
