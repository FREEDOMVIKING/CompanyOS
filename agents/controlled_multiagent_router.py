#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"multiagent_router_config.json"
ASSIGN=MEM/"specialist_assignment_plan.json"
STATE=MEM/"multiagent_router_state.json"
REPORT=MEM/"multiagent_router_report.json"
HEALTH=MEM/"multiagent_router_health.json"
QUEUE=MEM/"multiagent_work_queue.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def mode(role):
    return {
      "research":"research","strategy":"plan","product":"plan","engineering":"review",
      "operations":"plan","marketing":"research","finance":"analyze"
    }.get(role,"analyze")

def route():
    cfg=load(CFG,{})
    assignments=load(ASSIGN,{}).get("assignments",[])
    maximum=int(cfg.get("maximum_work_items_per_cycle",10))
    allowed=set(cfg.get("allowed_work_modes",[]))
    queued=[];blocked=[]

    for item in assignments[:maximum]:
        role=item.get("specialist_role","strategy")
        work_mode=mode(role)
        work={
          "work_id":item.get("assignment_id"),
          "opportunity_id":item.get("opportunity_id"),
          "title":item.get("title"),
          "specialist_role":role,
          "specialist":item.get("specialist"),
          "work_mode":work_mode,
          "instruction":item.get("instruction"),
          "attention_units":item.get("attention_units",0)
        }
        if work_mode not in allowed:
            blocked.append({**work,"status":"blocked","reason":"work_mode_not_allowed"})
            continue
        queued.append({**work,"status":"queued_internal","queued_at":now(),
          "execution_boundary":"internal_non_destructive_only"})

    payload={"generated_at":now(),"queued_count":len(queued),"work_items":queued}
    save(QUEUE,payload)
    report={"generated_at":now(),"queued_count":len(queued),"blocked_count":len(blocked),
      "queued":queued,"blocked":blocked,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_routed_at":now(),"queued_count":len(queued),"blocked_count":len(blocked)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"queued_count":len(queued)})
    return {"success":True,"status":"controlled_multiagent_routing_complete","report":report}

def status():
    return {"success":True,"status":"multiagent_router_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"queue":load(QUEUE,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=route() if a=="route" else status() if a=="status" else {"success":False,"allowed":["route","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
