#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"operations_observability_report.json"
STATE=MEM/"operations_observability_state.json"
HEALTH=MEM/"operations_observability_health.json"

FILES=[
 ("autonomy","autonomy_core_health.json"),
 ("phase23","phase23_health.json"),
 ("phase23_bundle2","phase23_bundle2_health.json"),
 ("phase23_bundle3","phase23_bundle3_health.json"),
 ("phase24","phase24_health.json"),
 ("phase24_bundle2","phase24_bundle2_health.json"),
 ("specialist_runtime","specialist_runtime_health.json"),
 ("provider","provider_health_health.json"),
 ("memory","persistent_memory_health.json")
]

def now():return datetime.now(timezone.utc).isoformat()
def load(name):
    p=MEM/name
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return {}
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def run():
    components=[];unhealthy=[]
    for label,name in FILES:
        data=load(name)
        healthy=bool(data.get("healthy",False))
        components.append({"component":label,"healthy":healthy,"data":data})
        if not healthy:unhealthy.append(label)
    payload={"generated_at":now(),"healthy":not unhealthy,"unhealthy_count":len(unhealthy),
      "unhealthy_components":unhealthy,"components":components}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"unhealthy_count":len(unhealthy)})
    save(HEALTH,{"healthy":not unhealthy,"last_checked_at":now(),"unhealthy_count":len(unhealthy)})
    return {"success":True,"status":"operations_observability_complete","report":payload}

r=run()
print(json.dumps(r,indent=2))
