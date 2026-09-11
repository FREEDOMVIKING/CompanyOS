#!/usr/bin/env python3
import json
from companyos_phase401_416 import CEOVentureBridge
from companyos_phase417_432 import AutonomousBuildBridge

thesis = {
    "name":"Contractor Bid Copilot",
    "customer":"small construction contractors",
    "core_problem":"turning scope into professional estimates and proposals is slow",
    "business_model":{"primary":"monthly SaaS subscription"},
}
validation = {"decision":{"decision":"go_to_mvp","confidence":0.88}}
venture = CEOVentureBridge().create_venture(thesis, validation)
build = AutonomousBuildBridge().prepare_build(venture)
print(json.dumps(build, indent=2))
