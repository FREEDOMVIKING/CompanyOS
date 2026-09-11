#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"specialist_bridge_config.json"
SOURCE=MEM/"governed_internal_work_results.json"
TARGET=MEM/"specialist_runtime_input_queue.json"
STATE=MEM/"specialist_bridge_state.json"
REPORT=MEM/"specialist_bridge_report.json"
HEALTH=MEM/"specialist_bridge_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def bridge():
    cfg=load(CFG,{})
    rows=load(SOURCE,{}).get("results",[])
    existing=load(TARGET,{"tasks":[]}).get("tasks",[])
    seen={x.get("work_id") for x in existing if x.get("work_id")}
    allowed=set(cfg.get("allowed_action_types",[]))
    maximum=int(cfg.get("maximum_tasks_per_cycle",10))
    added=[];blocked=[]

    for row in rows:
        if len(added)>=maximum: break
        if row.get("status")!="prepared_for_specialist_runtime": continue
        wid=row.get("work_id")
        if not wid or wid in seen: continue
        action=row.get("action_type")
        if action not in allowed:
            blocked.append({"work_id":wid,"reason":"action_type_not_allowed"})
            continue
        task={
          "work_id":wid,
          "plan_id":row.get("plan_id"),
          "decision_id":row.get("decision_id"),
          "opportunity_id":row.get("opportunity_id"),
          "action_type":action,
          "instruction":row.get("instruction"),
          "execution_boundary":"internal_non_destructive_only",
          "status":"queued_for_live_specialist",
          "queued_at":now()
        }
        existing.append(task);added.append(task);seen.add(wid)

    payload={"generated_at":now(),"task_count":len(existing),"tasks":existing}
    save(TARGET,payload)

    report={
      "generated_at":now(),
      "added_count":len(added),
      "blocked_count":len(blocked),
      "total_task_count":len(existing),
      "added":added,
      "blocked":blocked,
      "automatic_external_write":False,
      "automatic_customer_contact":False,
      "automatic_publication":False,
      "automatic_spending":False,
      "automatic_fund_transfer":False,
      "automatic_code_changes":False,
      "automatic_merge":False,
      "automatic_deploy":False,
      "automatic_destructive_actions":False
    }
    save(REPORT,report)
    save(STATE,{"last_bridged_at":now(),"added_count":len(added),"total_task_count":len(existing)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"task_count":len(existing)})
    return {"success":True,"status":"live_specialist_bridge_complete","report":report}

def status():
    return {"success":True,"status":"live_specialist_bridge_status",
      "state":load(STATE,{}),"health":load(HEALTH,{}),
      "report":load(REPORT,{}),"queue":load(TARGET,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=bridge() if a=="bridge" else status() if a=="status" else {"success":False,"allowed":["bridge","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
