#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";PLANS=MEM/"strategic_execution_plans.json";OUT=MEM/"agent_orchestration_queue.json";STATE=MEM/"agent_orchestration_state.json";HEALTH=MEM/"agent_orchestration_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def hid(x):return hashlib.sha256(str(x).encode()).hexdigest()[:18]
def run():
    rows=[];role_map={"evidence_validation":"research","strategy_design":"strategy","execution_mapping":"planning","risk_review":"review","decision_ready":"synthesis"}
    for p in load(PLANS,{}).get("plans",[]):
        for m in p.get("milestones",[]):
            rows.append({"task_id":hid(p.get("plan_id","")+"|"+m["name"]),"plan_id":p.get("plan_id"),"opportunity_id":p.get("opportunity_id"),"specialist_role":role_map.get(m["name"],"analysis"),"instruction":m.get("objective"),"status":"ready_for_internal_specialist","provider_route":"openai_primary_then_local_fallback","execution_boundary":"internal_non_destructive_only"})
    payload={"generated_at":now(),"task_count":len(rows),"tasks":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"task_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"agent_orchestration_complete","queue":payload}
print(json.dumps(run(),indent=2))
