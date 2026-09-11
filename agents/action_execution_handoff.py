#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"action_handoff_config.json"
SRC=MEM/"opportunity_ready_queue.json"
OUT=MEM/"execution_handoff_queue.json"
STATE=MEM/"action_handoff_state.json"
REPORT=MEM/"action_handoff_report.json"
HEALTH=MEM/"action_handoff_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2),encoding="utf-8"); t.replace(p)

def handoff():
    cfg=load(CFG,{})
    src=load(SRC,{})
    allowed=set(cfg.get("allowed_categories",[]))
    maximum=int(cfg.get("max_handoffs_per_cycle",10))
    accepted=[]; rejected=[]

    for item in src.get("actions",[])[:maximum]:
        cat=item.get("category","internal_read_only")
        if cat not in allowed:
            rejected.append({**item,"handoff_status":"rejected","reason":"category_not_allowed"})
            continue
        accepted.append({
            **item,
            "handoff_status":"approved_for_guarded_execution",
            "handed_off_at":now(),
            "requires_guarded_executor":True
        })

    payload={"generated_at":now(),"handoff_count":len(accepted),"actions":accepted}
    save(OUT,payload)

    report={
      "generated_at":now(),"accepted_count":len(accepted),"rejected_count":len(rejected),
      "accepted":accepted,"rejected":rejected,
      "automatic_external_write":False,"automatic_customer_contact":False,
      "automatic_publication":False,"automatic_spending":False,
      "automatic_code_changes":False,"automatic_merge":False,"automatic_deploy":False,
      "automatic_destructive_actions":False
    }
    save(REPORT,report)
    save(STATE,{"last_handoff_at":now(),"accepted_count":len(accepted),"rejected_count":len(rejected)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"handoff_count":len(accepted)})
    return {"success":True,"status":"action_execution_handoff_complete","report":report}

def status():
    return {"success":True,"status":"action_execution_handoff_status",
            "state":load(STATE,{}),"health":load(HEALTH,{}),
            "report":load(REPORT,{}),"queue":load(OUT,{})}

cmd=sys.argv[1] if len(sys.argv)>1 else "status"
res=handoff() if cmd=="handoff" else status() if cmd=="status" else {"success":False,"allowed":["handoff","status"]}
print(json.dumps(res,indent=2))
raise SystemExit(0 if res.get("success") else 1)
