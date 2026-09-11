#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"autonomy_watchdog_report.json"; HEALTH=MEM/"autonomy_watchdog_health.json"

CHECKS=[
 ("phase23_health.json","phase23"),
 ("autonomy_core_health.json","autonomy"),
 ("specialist_runtime_health.json","specialist_runtime"),
 ("provider_health_health.json","provider"),
 ("persistent_memory_health.json","memory")
]

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d

def run():
    results=[];failures=[]
    for name,label in CHECKS:
        p=MEM/name
        data=load(p,{})
        ok=bool(data.get("healthy",False)) if data else False
        results.append({"component":label,"healthy":ok,"data":data})
        if not ok:failures.append(label)
    payload={"generated_at":now(),"healthy":not failures,"failure_count":len(failures),
      "failed_components":failures,"checks":results}
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    HEALTH.write_text(json.dumps({"healthy":not failures,"last_checked_at":now(),
      "failure_count":len(failures)},indent=2),encoding="utf-8")
    return {"success":True,"status":"autonomy_watchdog_complete","report":payload}

r=run()
print(json.dumps(r,indent=2))
