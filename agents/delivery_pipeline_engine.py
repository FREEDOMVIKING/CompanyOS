#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle4_config.json"
PROJECTS=MEM/"project_execution_registry.json"
MILESTONES=MEM/"project_milestones.json"
OUT=MEM/"delivery_pipeline.json"
STATE=MEM/"delivery_pipeline_state.json"
HEALTH=MEM/"delivery_pipeline_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def did(seed):return hashlib.sha256(str(seed).encode()).hexdigest()[:18]

def build():
    cfg=load(CFG,{})
    projects=load(PROJECTS,{}).get("projects",[])
    ms={x.get("project_id"):x for x in load(MILESTONES,{}).get("projects",[])}
    rows=[]
    for p in projects[:int(cfg.get("maximum_delivery_items",50))]:
        pm=ms.get(p.get("project_id"),{})
        rows.append({
          "delivery_id":did(p.get("project_id")),
          "project_id":p.get("project_id"),
          "title":p.get("title"),
          "current_stage":p.get("stage"),
          "milestones":pm.get("milestones",[]),
          "status":"internal_delivery_planning",
          "external_delivery_authorized":False,
          "created_at":now()
        })
    payload={"generated_at":now(),"delivery_count":len(rows),"deliveries":rows}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"delivery_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"delivery_count":len(rows)})
    return {"success":True,"status":"delivery_pipeline_complete","pipeline":payload}

def status():
    return {"success":True,"status":"delivery_pipeline_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"pipeline":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
