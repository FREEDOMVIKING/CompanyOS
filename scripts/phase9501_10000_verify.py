#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.productionruntime import *

root=Path(tempfile.mkdtemp())

assert RuntimeProfile().build()["persistent"] is True
assert StartupPreflight().evaluate({
    "state_store":True,"checkpoint":True,"queue":True,"memory":True,
    "approval_queue":True,"health":True,"config":True})["passed"]

graph=ServiceGraph().build()
assert "ceo" in graph["nodes"]

assert ContinuousCompanyCycle().plan("discover")["next_stage"]=="research"
assert MissionRouter().route({"mission_type":"build"})["department"]=="product"

cp=CheckpointChain(root)
cp.save({"x":1})
assert cp.latest()

assert ProductionRuntimeStatus().status()["status"]=="phase10000_autonomous_company_production_runtime_ready"

print(json.dumps({
    "success":True,
    "status":"phase9501_10000_verification_passed",
    "cycle_status":"phase10000_autonomous_company_production_runtime_ready"
},indent=2))
