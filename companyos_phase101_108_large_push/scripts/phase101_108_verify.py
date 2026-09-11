#!/usr/bin/env python3
import json
from companyos_phase101_108 import *
assert GoalTree().build("grow",[{"objective":"sell","metric":"mrr","target":1000}])["count"]==1
assert StrategyEngine().rank([{"name":"a","value":1,"evidence":1,"speed":1,"risk":0}])[0]["name"]=="a"
assert DelegationSupervisor().review([{"complete":True,"quality":.9}])[0]["accepted"] is True
assert ExecutionWatchdog().inspect([{"id":"x","status":"failed"}])["attention_required"] is True
assert EconomicsEngine().analyze(10,2,100,20)["funds_moved"] is False
assert GrowthLoop().recommend({"acquisition":.9,"activation":.2,"retention":.8,"referral":.7})["weakest_stage"]=="activation"
assert RecoveryDirector().direct({"severity":"critical"})["automatic_destructive_action"] is False
c=AutonomousCEOLoop().run({"goal":"build sustainable company",
"objectives":[{"objective":"validate demand","metric":"qualified_leads","target":10}],
"strategies":[{"name":"controlled validation","value":.9,"evidence":.8,"speed":.8,"risk":.2}],
"price":100,"variable_cost":20,"fixed_cost":500,"customers":10,
"growth_metrics":{"acquisition":.5,"activation":.6,"retention":.7,"referral":.4}})
assert c["success"] and not c["external_action_taken"] and not c["financial_action_taken"] and not c["irreversible_action_taken"]
print(json.dumps({"success":True,"status":"phase101_108_verification_passed","cycle_status":c["status"],
"external_action_taken":c["external_action_taken"],"financial_action_taken":c["financial_action_taken"],
"irreversible_action_taken":c["irreversible_action_taken"]},indent=2))
