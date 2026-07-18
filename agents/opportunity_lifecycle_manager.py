#!/usr/bin/env python3
import json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"opportunity_lifecycle_config.json"
PORT=MEM/"rebalanced_opportunity_portfolio.json"
STATE=MEM/"opportunity_lifecycle_state.json"
REPORT=MEM/"opportunity_lifecycle_report.json"
HEALTH=MEM/"opportunity_lifecycle_health.json"
ARCHIVE=MEM/"retired_opportunities.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2),encoding="utf-8")
    t.replace(p)
def score(x):
    try:return float(x.get("final_opportunity_score",0) or 0)
    except:return 0.0

def evaluate():
    cfg=load(CFG,{})
    rows=load(PORT,{}).get("opportunities",[])
    minimum=float(cfg.get("minimum_keep_score",50))
    max_failed=int(cfg.get("maximum_failed_cycles",3))
    archive=load(ARCHIVE,{"retired":[]})
    retired=archive.setdefault("retired",[])
    active=[]; newly_retired=[]

    for row in rows:
        failures=int(row.get("failed_cycles",0) or 0)
        reason=None
        if score(row)<minimum:
            reason="score_below_keep_threshold"
        elif failures>=max_failed:
            reason="repeated_failed_cycles"

        if reason:
            item={
              "id":row.get("id"),"title":row.get("title"),
              "category":row.get("category"),
              "final_opportunity_score":row.get("final_opportunity_score"),
              "retired_at":now(),"reason":reason,
              "status":"retired_internal"
            }
            retired.append(item);newly_retired.append(item)
        else:
            x=dict(row);x["lifecycle_status"]="active";active.append(x)

    archive["updated_at"]=now()
    save(ARCHIVE,archive)

    report={
      "generated_at":now(),"evaluated_count":len(rows),
      "active_count":len(active),"retired_count":len(newly_retired),
      "active":active,"newly_retired":newly_retired,
      "automatic_external_write":False,"automatic_customer_contact":False,
      "automatic_publication":False,"automatic_spending":False,
      "automatic_code_changes":False,"automatic_merge":False,
      "automatic_deploy":False,"automatic_destructive_actions":False
    }
    save(REPORT,report)
    save(STATE,{"last_evaluated_at":now(),"active_count":len(active),
                "retired_count":len(newly_retired)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),
                 "evaluated_count":len(rows)})
    return {"success":True,"status":"opportunity_lifecycle_evaluation_complete","report":report}

def status():
    return {"success":True,"status":"opportunity_lifecycle_status",
            "state":load(STATE,{}),"health":load(HEALTH,{}),
            "report":load(REPORT,{}),"archive":load(ARCHIVE,{"retired":[]})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=evaluate() if a=="evaluate" else status() if a=="status" else {
  "success":False,"allowed":["evaluate","status"]
}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
