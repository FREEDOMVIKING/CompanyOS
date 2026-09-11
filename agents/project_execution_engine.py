#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle2_config.json"
TASKS=MEM/"persistent_task_registry.json"
VALIDATED=MEM/"validated_business_opportunities.json"
OUT=MEM/"project_execution_registry.json"
STATE=MEM/"project_execution_state.json"
HEALTH=MEM/"project_execution_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def pid(seed):return hashlib.sha256(str(seed).encode()).hexdigest()[:18]

def build():
    cfg=load(CFG,{})
    validated=[x for x in load(VALIDATED,{}).get("opportunities",[])
               if x.get("validation_status")=="validated_internal_candidate"]
    tasks=load(TASKS,{}).get("tasks",[])
    projects=[]
    for i,o in enumerate(validated[:int(cfg.get("maximum_projects",20))],1):
        title=o.get("title") or f"Project {i}"
        projects.append({
          "project_id":pid(o.get("id") or title),
          "title":title,
          "source_opportunity_id":o.get("id"),
          "validation_score":o.get("validation_score"),
          "stage":"discovery",
          "stages":[
            {"name":"discovery","status":"active"},
            {"name":"validation","status":"pending"},
            {"name":"planning","status":"pending"},
            {"name":"internal_execution","status":"pending"},
            {"name":"measurement","status":"pending"}
          ],
          "linked_task_count":sum(1 for t in tasks if t.get("title")==title),
          "authority":"internal_non_destructive_only",
          "created_at":now()
        })
    payload={"generated_at":now(),"project_count":len(projects),"projects":projects}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"project_count":len(projects)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"project_count":len(projects)})
    return {"success":True,"status":"project_execution_registry_complete","registry":payload}

def status():
    return {"success":True,"status":"project_execution_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"registry":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
