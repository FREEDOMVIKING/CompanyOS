#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"governed_execution_queue_config.json"
PLANS=MEM/"governed_internal_execution_plans.json"
QUEUE=MEM/"governed_internal_work_queue.json"
STATE=MEM/"governed_execution_queue_state.json"
REPORT=MEM/"governed_execution_queue_report.json"
HEALTH=MEM/"governed_execution_queue_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def enqueue():
    cfg=load(CFG,{})
    plans=load(PLANS,{}).get("plans",[])
    old=load(QUEUE,{"work_items":[]}).get("work_items",[])
    existing={x.get("work_id"):x for x in old if x.get("work_id")}
    allowed_auth=set(cfg.get("allowed_authority",[]))
    allowed_types=set(cfg.get("allowed_action_types",[]))
    maximum=int(cfg.get("maximum_items_per_cycle",25))
    added=[];blocked=[]

    for plan in plans:
        if plan.get("execution_authority") not in allowed_auth:
            blocked.append({"plan_id":plan.get("plan_id"),"reason":"authority_not_allowed"});continue
        for step in plan.get("steps",[]):
            if len(added)>=maximum: break
            action_type=step.get("action_type")
            if action_type not in allowed_types:
                blocked.append({"plan_id":plan.get("plan_id"),"step":step.get("step"),"reason":"action_type_not_allowed"});continue
            wid=f"{plan.get('plan_id')}-step-{step.get('step')}"
            if wid in existing: continue
            item={
              "work_id":wid,"plan_id":plan.get("plan_id"),"decision_id":plan.get("decision_id"),
              "opportunity_id":plan.get("opportunity_id"),"title":plan.get("title"),
              "step":step.get("step"),"action_type":action_type,"instruction":step.get("instruction"),
              "execution_authority":"internal_non_destructive_only","status":"queued",
              "attempts":0,"queued_at":now()
            }
            existing[wid]=item;added.append(item)

    all_items=list(existing.values())
    payload={"generated_at":now(),"queued_count":len(all_items),"work_items":all_items}
    save(QUEUE,payload)
    report={"generated_at":now(),"added_count":len(added),"total_queued_count":len(all_items),
      "blocked_count":len(blocked),"added":added,"blocked":blocked,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_enqueued_at":now(),"added_count":len(added),"total_queued_count":len(all_items)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"total_queued_count":len(all_items)})
    return {"success":True,"status":"governed_internal_queue_complete","report":report}

def status():
    return {"success":True,"status":"governed_execution_queue_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"queue":load(QUEUE,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=enqueue() if a=="enqueue" else status() if a=="status" else {"success":False,"allowed":["enqueue","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
