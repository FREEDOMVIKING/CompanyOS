#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase25_bundle2_config.json"
SRC=MEM/"governed_internal_work_results.json"
OUT=MEM/"decomposed_ai_tasks.json"
STATE=MEM/"task_decomposition_state.json"
HEALTH=MEM/"task_decomposition_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def hid(x):return hashlib.sha256(str(x).encode()).hexdigest()[:18]

def run():
    cfg=load(CFG,{})
    rows=[]
    parents=load(SRC,{}).get("results",[])[:int(cfg.get("maximum_parent_tasks",20))]
    for p in parents:
        if p.get("status") not in ("prepared_for_specialist_runtime","pending","completed"): continue
        parent_id=p.get("work_id") or hid(p)
        action=p.get("action_type","analysis")
        templates=[
          ("research","Gather and organize relevant internal evidence"),
          ("analysis","Analyze options, constraints, risks, and tradeoffs"),
          ("planning","Create a practical internal execution plan"),
          ("review","Review assumptions, gaps, and failure modes"),
          ("synthesis","Summarize the strongest internal recommendation")
        ]
        subtasks=[]
        for role,inst in templates[:int(cfg.get("maximum_subtasks_per_parent",5))]:
            subtasks.append({
              "subtask_id":hid(parent_id+"|"+role),
              "parent_work_id":parent_id,
              "role":role,
              "instruction":f"{inst}. Parent action type: {action}.",
              "status":"ready_for_internal_delegation",
              "execution_boundary":"internal_non_destructive_only"
            })
        rows.append({"parent_work_id":parent_id,"subtask_count":len(subtasks),"subtasks":subtasks})
    payload={"generated_at":now(),"parent_count":len(rows),"parents":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"parent_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"task_decomposition_complete","report":payload}

print(json.dumps(run(),indent=2))
