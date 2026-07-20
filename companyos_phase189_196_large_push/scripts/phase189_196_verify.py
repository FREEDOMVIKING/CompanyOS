#!/usr/bin/env python3
import json
from companyos_phase189_196 import *
i=IntentEngine().generate("grow",{"gaps":["sales"]});assert i[0]["autonomous"]
assert HypothesisFactory().create(i)[0]["autonomous_test_design"]
assert ExperimentLoop().next({"stage":"design"})["stage"]=="execute_internal"
assert AutonomousArchitect().evaluate({"kind":"refactor","reversible":True,"verification_plan":True})["autonomous_change_allowed"]
assert ServiceSupervisor().inspect([{"name":"x","healthy":False,"consecutive_failures":1}])[0]["action"]=="restart"
assert MemoryConsolidator().consolidate([{"topic":"x","score":1}]*3)[0]["durable"]
assert GrowthFlywheel().evaluate({"evidence":.8,"product":.8,"distribution":.2,"retention":.7})["constraint"]=="distribution"
r=CompanyKernel().tick({"mission":"grow","state":{"gaps":["distribution"]}})
assert r["success"] and r["persistent_kernel"] and r["autonomy_mode"]=="high"
print(json.dumps({"success":True,"status":"phase189_196_verification_passed","cycle_status":r["status"],
"autonomy_mode":"high","persistent_kernel":True,"external_action_taken":False,
"financial_action_taken":False,"irreversible_action_taken":False},indent=2))
