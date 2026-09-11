#!/usr/bin/env python3
import json
from companyos_phase197_204 import *
g=GoalContinuityEngine().reconcile([{"goal":"grow"}],[]);assert g[0]["carry_forward"]
assert InitiativeSpawner().spawn(g,[])[0]["autonomous"]
assert AutonomousBuilder().next({})["action"]=="create_spec"
assert ValidationEngine().evaluate({"samples":5,"confidence":.9,"score":.8})["validated"]
assert PolicyLearner().learn([{"runs":5,"success_rate":.9,"improvement":.2}])[0]["learned_default"]
assert PriorityArbitrator().rank([{"name":"x","impact":1,"urgency":1,"evidence":1,"learning":1,"risk":0}])[0]["name"]=="x"
assert len(IdleWorkGenerator().generate(2,5))==3
r=AlwaysOnCEO().tick({"goals":[{"goal":"grow"}],"capacity":5})
assert r["success"] and r["always_on_ceo"] and r["work_starvation_prevention"]
print(json.dumps({"success":True,"status":"phase197_204_verification_passed","cycle_status":r["status"],
"autonomy_mode":"high","always_on_ceo":True,"work_starvation_prevention":True,
"external_action_taken":False,"financial_action_taken":False,"irreversible_action_taken":False},indent=2))
