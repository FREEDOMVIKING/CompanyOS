#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.autonomyops import ObjectiveEngine, PriorityEngine, CycleMemory, AutonomyOpsStatus

root = Path(tempfile.mkdtemp())

obj = ObjectiveEngine().choose([])
assert isinstance(obj, str) and obj

ranked = PriorityEngine().rank([
    {"name":"a","value":0.9,"confidence":0.8,"urgency":0.7,"risk":0.2,"effort":0.3},
    {"name":"b","value":0.5,"confidence":0.5,"urgency":0.5,"risk":0.5,"effort":0.5},
])
assert ranked[0]["name"] == "a"

mem = CycleMemory(root)
mem.append({"objective":"x","resolved":True})
assert len(mem.recent()) == 1

assert AutonomyOpsStatus().status()["status"] == "phase20000_continuous_autonomy_layer_ready"

print(json.dumps({
    "success": True,
    "status": "phase19001_20000_verification_passed",
    "cycle_status": "phase20000_continuous_autonomy_layer_ready"
}, indent=2))
