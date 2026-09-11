#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.runtime import CEOCompanyRuntime

root=Path.home()/"companyos"
rt=CEOCompanyRuntime(root)

boot=rt.bootstrap(
    cadence={
        "daily":["review critical metrics","execute highest priority work","resolve incidents","update decision memory"],
        "weekly":["review venture scorecards","reallocate budget and agents"],
        "monthly":["review strategy horizons"]
    },
    ventures=[
        {"venture_id":"venture_a","priority_score":.9,"requested_slots":2},
        {"venture_id":"venture_b","priority_score":.6,"requested_slots":1},
    ],
    departments=["operations","product","research"]
)

cycle=rt.run_cycle(["operations","product","research"])
status=rt.status()
recovery=rt.recover()

print(json.dumps({
    "bootstrap":boot,
    "cycle":cycle,
    "status":status,
    "recovery":recovery
},indent=2,default=str))
