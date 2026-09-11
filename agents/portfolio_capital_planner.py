#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_bundle3_config.json"
PLAN=MEM/"strategic_30_day_plan.json"
OUT=MEM/"portfolio_resource_plan.json"
STATE=MEM/"portfolio_resource_plan_state.json"
HEALTH=MEM/"portfolio_resource_plan_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def allocate():
    cfg=load(CFG,{})
    actions=load(PLAN,{}).get("actions",[])
    total_units=int(cfg.get("abstract_resource_units",100))
    positive=[max(float(a.get("score",50) or 50),1.0) for a in actions]
    denom=sum(positive) or 1
    rows=[]
    remaining=total_units
    for i,a in enumerate(actions):
        units=round(total_units*positive[i]/denom)
        if i==len(actions)-1: units=remaining
        remaining-=units
        rows.append({
          "action_id":a.get("id"),"title":a.get("title"),
          "resource_units":max(units,0),
          "resource_type":"abstract_internal_attention_units",
          "status":"planned_only"
        })
    payload={"generated_at":now(),"total_resource_units":total_units,
      "allocation_count":len(rows),"allocations":rows,
      "note":"These are abstract internal planning units, not money or real financial commitments."}
    save(OUT,payload);save(STATE,{"last_allocated_at":now(),"allocation_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"allocation_count":len(rows)})
    return {"success":True,"status":"portfolio_resource_planning_complete","plan":payload}

def status():
    return {"success":True,"status":"portfolio_resource_plan_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"plan":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=allocate() if a=="allocate" else status() if a=="status" else {"success":False,"allowed":["allocate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
