#!/usr/bin/env python3
import json
from companyos_phase401_416 import CEOVentureBridge

thesis = {
    "name":"Contractor Bid Copilot",
    "customer":"small construction contractors",
    "core_problem":"turning scope into professional estimates and proposals is slow",
    "business_model":{"primary":"monthly SaaS subscription"},
}
validation = {"decision":{"decision":"go_to_mvp","confidence":0.88}}

print(json.dumps(CEOVentureBridge().create_venture(thesis, validation), indent=2))
