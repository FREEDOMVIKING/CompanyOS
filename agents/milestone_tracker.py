#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle2_config.json"
PROJECTS=MEM/"project_execution_registry.json"
OUT=MEM/"project_milestones.json"
STATE=MEM/"milestone_state.json"
HEALTH=MEM/"milestone_health.json"

TEMPLATE=[
 ("evidence_review","Evidence reviewed"),
 ("success_criteria","Success criteria defined"),
 ("dependency_map","Dependencies mapped"),
 ("execution_plan","Internal execution plan prepared"),
 ("pilot_ready","Governed pilot ready"),
 ("measurement","Measurement framework prepared")
]

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def mid(pid,name):return hashlib.sha256(f"{pid}|{name}".encode()).hexdigest()[:18]

def build():
    cfg=load(CFG,{})
    projects=load(PROJECTS,{}).get("projects",[])
    maxm=int(cfg.get("maximum_milestones_per_project",8))
    rows=[]
    for p in projects:
        milestones=[]
        for key,title in TEMPLATE[:maxm]:
            milestones.append({
              "milestone_id":mid(p.get("project_id"),key),
              "name":key,"title":title,"status":"pending"
            })
        rows.append({"project_id":p.get("project_id"),"title":p.get("title"),
          "milestone_count":len(milestones),"milestones":milestones})
    payload={"generated_at":now(),"project_count":len(rows),"projects":rows}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"project_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"project_count":len(rows)})
    return {"success":True,"status":"milestone_tracker_complete","report":payload}

def status():
    return {"success":True,"status":"milestone_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
