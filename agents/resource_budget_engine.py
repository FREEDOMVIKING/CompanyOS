#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle2_config.json"
PROJECTS=MEM/"project_execution_registry.json"
OUT=MEM/"project_resource_budgets.json"
STATE=MEM/"resource_budget_state.json"
HEALTH=MEM/"resource_budget_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def allocate():
    cfg=load(CFG,{})
    projects=load(PROJECTS,{}).get("projects",[])
    total=int(cfg.get("abstract_budget_units",100))
    weights=[max(float(p.get("validation_score",50) or 50),1) for p in projects]
    denom=sum(weights) or 1
    rows=[];remaining=total
    for i,p in enumerate(projects):
        units=round(total*weights[i]/denom)
        if i==len(projects)-1:units=remaining
        remaining-=units
        rows.append({
          "project_id":p.get("project_id"),"title":p.get("title"),
          "budget_units":max(units,0),
          "budget_type":"abstract_internal_capacity_units",
          "status":"planned_only"
        })
    payload={"generated_at":now(),"total_budget_units":total,"allocations":rows,
      "note":"These units are internal planning capacity, not money or authorization to spend."}
    save(OUT,payload);save(STATE,{"last_allocated_at":now(),"allocation_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"allocation_count":len(rows)})
    return {"success":True,"status":"resource_budget_complete","report":payload}

def status():
    return {"success":True,"status":"resource_budget_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=allocate() if a=="allocate" else status() if a=="status" else {"success":False,"allowed":["allocate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
