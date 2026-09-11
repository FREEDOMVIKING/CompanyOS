#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.selfimprove import *

root=Path(tempfile.mkdtemp())
base=PerformanceBaseline().build({"latency":2,"success_rate":.99,"cost_per_cycle":2,"recovery_rate":.95,"throughput":10})
assert base["success_rate"]==.99
assert BottleneckDetector().detect(base,{"min_success_rate":.95})==[]
p=SafePatchGenerator().propose("router","optimize",True)
v=SandboxValidator().validate(p,[{"passed":True}])
assert v["safe_for_canary"]
assert RegressionGuard().compare(base,base)["passed"]
assert SelfImprovementBoundary().evaluate({"kind":"safety_policy"})["requires_approval"]
assert SelfImprovementStatus().status()["status"]=="phase10500_self_improving_autonomous_enterprise_ready"

print(json.dumps({
    "success":True,
    "status":"phase10001_10500_verification_passed",
    "cycle_status":"phase10500_self_improving_autonomous_enterprise_ready"
},indent=2))
