#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_config.json"
RESEARCH=MEM/"research_mission_queue.json"
TARGET=MEM/"specialist_runtime_input_queue.json"
STATE=MEM/"research_bridge_state.json"
HEALTH=MEM/"research_bridge_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def wid(mid):return "research-"+hashlib.sha256(str(mid).encode()).hexdigest()[:18]

def bridge():
    cfg=load(CFG,{})
    missions=load(RESEARCH,{}).get("missions",[])
    q=load(TARGET,{"tasks":[]});tasks=q.get("tasks",[])
    seen={x.get("work_id") for x in tasks}
    added=[]
    for m in missions[:int(cfg.get("maximum_research_tasks_per_cycle",10))]:
        work_id=wid(m.get("mission_id"))
        if work_id in seen:continue
        instruction=(m.get("title","Research mission")+"\nQuestions:\n- "+"\n- ".join(m.get("questions",[])))
        task={
          "work_id":work_id,"plan_id":"phase24-research","decision_id":None,
          "opportunity_id":m.get("source_action_id"),"action_type":"research",
          "instruction":instruction,"execution_boundary":"internal_non_destructive_only",
          "status":"queued_for_live_specialist","queued_at":now()
        }
        tasks.append(task);added.append(task);seen.add(work_id)
    payload={"generated_at":now(),"task_count":len(tasks),"tasks":tasks}
    save(TARGET,payload);save(STATE,{"last_bridged_at":now(),"added_count":len(added),"task_count":len(tasks)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"task_count":len(tasks)})
    return {"success":True,"status":"research_specialist_bridge_complete","added_count":len(added)}

def status():
    return {"success":True,"status":"research_specialist_bridge_status","state":load(STATE,{}),"health":load(HEALTH,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=bridge() if a=="bridge" else status() if a=="status" else {"success":False,"allowed":["bridge","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
