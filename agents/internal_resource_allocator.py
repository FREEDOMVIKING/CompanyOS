#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"resource_allocation_config.json"
PRIORITIES=MEM/"portfolio_resource_priorities.json"
STATE=MEM/"resource_allocation_state.json"
REPORT=MEM/"resource_allocation_report.json"
HEALTH=MEM/"resource_allocation_health.json"
PLAN=MEM/"internal_resource_plan.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def num(v,d=0):
    try:return float(v)
    except:return float(d)

def allocate():
    cfg=load(CFG,{})
    rows=load(PRIORITIES,{}).get("candidates",[])
    maximum=int(cfg.get("maximum_priority_projects",5))
    total=max(0,int(cfg.get("total_attention_units",100)))
    minimum=max(0,int(cfg.get("minimum_units_per_project",5)))
    rows=rows[:maximum]
    weights=[max(0.0,num(x.get("resource_readiness_score",0))) for x in rows]
    weight_sum=sum(weights)
    allocations=[]

    if rows:
        base=min(minimum,total//len(rows))
        remaining=max(0,total-(base*len(rows)))
        raw=[(remaining*(w/weight_sum) if weight_sum else remaining/len(rows)) for w in weights]
        extras=[int(x) for x in raw]
        leftover=remaining-sum(extras)
        order=sorted(range(len(raw)),key=lambda i:raw[i]-extras[i],reverse=True)
        for i in order[:leftover]: extras[i]+=1
        for row,extra in zip(rows,extras):
            allocations.append({
              "id":row.get("id"),"title":row.get("title"),"category":row.get("category"),
              "resource_readiness_score":row.get("resource_readiness_score"),
              "attention_units":base+extra,
              "allocation_type":"internal_planning_priority"
            })

    plan={"generated_at":now(),"total_attention_units":total,
          "allocated_units":sum(x["attention_units"] for x in allocations),
          "allocations":allocations,
          "note":"Attention units are internal planning weights only; no money or external resources are moved."}
    save(PLAN,plan)

    report={"generated_at":now(),"candidate_count":len(rows),"allocation_count":len(allocations),
      "allocations":allocations,
      "automatic_external_write":False,"automatic_customer_contact":False,
      "automatic_publication":False,"automatic_spending":False,"automatic_fund_transfer":False,
      "automatic_code_changes":False,"automatic_merge":False,"automatic_deploy":False,
      "automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_allocated_at":now(),"allocation_count":len(allocations),
      "allocated_units":plan["allocated_units"]})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"allocation_count":len(allocations)})
    return {"success":True,"status":"internal_resource_allocation_complete","report":report,"plan":plan}

def status():
    return {"success":True,"status":"internal_resource_allocation_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"plan":load(PLAN,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=allocate() if a=="allocate" else status() if a=="status" else {"success":False,"allowed":["allocate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
