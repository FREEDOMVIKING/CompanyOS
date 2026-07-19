#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
TASKS=MEM/"decomposed_ai_tasks.json"
MODELS=MEM/"model_capability_registry.json"
OUT=MEM/"specialist_delegation_plan.json"
STATE=MEM/"specialist_delegation_state.json"
HEALTH=MEM/"specialist_delegation_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    models=load(MODELS,{}).get("models",[])
    openai=next((m for m in models if m.get("provider")=="openai"),{})
    local=next((m for m in models if m.get("provider")=="local_llama"),{})
    rows=[]
    for parent in load(TASKS,{}).get("parents",[]):
        for s in parent.get("subtasks",[]):
            preferred="openai" if openai.get("available") else "local_llama"
            fallback="local_llama" if local.get("available") else None
            rows.append({
              "subtask_id":s.get("subtask_id"),
              "parent_work_id":s.get("parent_work_id"),
              "specialist_role":s.get("role"),
              "preferred_provider":preferred,
              "fallback_provider":fallback,
              "status":"assigned_internal",
              "execution_boundary":"internal_non_destructive_only"
            })
    payload={"generated_at":now(),"assignment_count":len(rows),"assignments":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"assignment_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"specialist_delegation_complete","plan":payload}

print(json.dumps(run(),indent=2))
