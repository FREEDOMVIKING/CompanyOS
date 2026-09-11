#!/usr/bin/env python3
from __future__ import annotations
import json, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_config.json"
STRATEGIC=MEM/"strategic_30_day_plan.json"
RESEARCH=MEM/"research_mission_queue.json"
IMPROVEMENTS=MEM/"governed_improvement_queue.json"
OUT=MEM/"persistent_task_registry.json"
STATE=MEM/"task_lifecycle_state.json"
HEALTH=MEM/"task_lifecycle_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2),encoding="utf-8"); t.replace(p)
def tid(kind,key): return hashlib.sha256(f"{kind}|{key}".encode()).hexdigest()[:20]

def sync():
    cfg=load(CFG,{})
    existing=load(OUT,{"tasks":[]}).get("tasks",[])
    by_id={x.get("task_id"):x for x in existing if x.get("task_id")}
    added=[]

    for a in load(STRATEGIC,{}).get("actions",[]):
        task_id=tid("strategic",a.get("id") or a.get("title"))
        if task_id not in by_id:
            by_id[task_id]={
              "task_id":task_id,"source":"strategic_plan","title":a.get("title"),
              "category":a.get("category"),"priority":a.get("priority",50),
              "status":"planned","authority":"internal_non_destructive_only",
              "created_at":now(),"updated_at":now()
            };added.append(by_id[task_id])

    for r in load(RESEARCH,{}).get("missions",[]):
        task_id=tid("research",r.get("mission_id"))
        if task_id not in by_id:
            by_id[task_id]={
              "task_id":task_id,"source":"research_mission","title":r.get("title"),
              "category":"research","priority":60,
              "status":"queued","authority":"internal_non_destructive_only",
              "created_at":now(),"updated_at":now()
            };added.append(by_id[task_id])

    for p in load(IMPROVEMENTS,{}).get("items",[]):
        task_id=tid("improvement",p.get("id"))
        if task_id not in by_id:
            by_id[task_id]={
              "task_id":task_id,"source":"improvement_queue","title":p.get("title"),
              "category":p.get("category","improvement"),"priority":p.get("priority",50),
              "status":"awaiting_governed_internal_review","authority":"none",
              "created_at":now(),"updated_at":now()
            };added.append(by_id[task_id])

    tasks=list(by_id.values())[:int(cfg.get("maximum_active_tasks",100))]
    payload={"generated_at":now(),"task_count":len(tasks),"tasks":tasks}
    save(OUT,payload)
    save(STATE,{"last_synced_at":now(),"added_count":len(added),"task_count":len(tasks)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"task_count":len(tasks)})
    return {"success":True,"status":"task_lifecycle_sync_complete","added_count":len(added),"registry":payload}

def status():
    return {"success":True,"status":"task_lifecycle_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"registry":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=sync() if a=="sync" else status() if a=="status" else {"success":False,"allowed":["sync","status"]}
print(json.dumps(r,indent=2)); raise SystemExit(0 if r.get("success") else 1)
