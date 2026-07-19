#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
WORK=MEM/"governed_internal_work_results.json"
PROVIDER=MEM/"ai_provider_health_report.json"
OUT=MEM/"ai_task_routing_plan.json"
STATE=MEM/"ai_task_router_state.json"
HEALTH=MEM/"ai_task_router_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    provider=load(PROVIDER,{})
    rows=[]
    for item in load(WORK,{}).get("results",[]):
        if item.get("status") not in ("prepared_for_specialist_runtime","pending"): continue
        rows.append({
          "work_id":item.get("work_id"),
          "action_type":item.get("action_type"),
          "primary_provider":"openai",
          "fallback_provider":"local_llama",
          "route":"primary_then_local_fallback",
          "local_available":provider.get("fallback",{}).get("reachable",False),
          "execution_boundary":"internal_non_destructive_only"
        })
    payload={"generated_at":now(),"route_count":len(rows),"routes":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"route_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"ai_task_routing_complete","plan":payload}

print(json.dumps(run(),indent=2))
