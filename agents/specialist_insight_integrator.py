#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"specialist_insight_config.json"
RESULTS=MEM/"specialist_work_results.json"
STATE=MEM/"specialist_insight_state.json"; REPORT=MEM/"specialist_insight_report.json"
HEALTH=MEM/"specialist_insight_health.json"; OUT=MEM/"ceo_specialist_insights.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def num(v,d=0):
    try:return float(v)
    except:return float(d)

def integrate():
    cfg=load(CFG,{})
    rows=load(RESULTS,{}).get("results",[])
    maximum=int(cfg.get("maximum_insights_per_cycle",20))
    require_completed=bool(cfg.get("require_completed_result",True))
    minimum=num(cfg.get("minimum_confidence",.5))
    accepted=[];pending=[];rejected=[]

    for row in rows[:maximum]:
        status=str(row.get("status",""))
        actual=row.get("actual_result")
        if require_completed and (status not in ("completed","validated") or not isinstance(actual,dict)):
            pending.append({"result_id":row.get("result_id"),"reason":"awaiting_completed_specialist_output"})
            continue
        confidence=num(actual.get("confidence",0) if isinstance(actual,dict) else 0)
        if confidence<minimum:
            rejected.append({"result_id":row.get("result_id"),"reason":"confidence_below_threshold",
                             "confidence":confidence})
            continue
        accepted.append({
          "insight_id":f"{row.get('result_id')}-insight",
          "opportunity_id":row.get("opportunity_id"),"title":row.get("title"),
          "specialist_role":row.get("specialist_role"),"specialist":row.get("specialist"),
          "confidence":confidence,
          "summary":actual.get("summary"),"findings":actual.get("findings",[]),
          "recommendations":actual.get("recommendations",[]),"risks":actual.get("risks",[]),
          "next_internal_actions":actual.get("next_internal_actions",[]),
          "decision_status":"available_for_ceo_reasoning",
          "integrated_at":now()
        })

    payload={"generated_at":now(),"insight_count":len(accepted),"insights":accepted,
             "note":"Insights inform internal CEO reasoning only; they do not authorize external actions."}
    save(OUT,payload)
    report={"generated_at":now(),"accepted_count":len(accepted),"pending_count":len(pending),
      "rejected_count":len(rejected),"accepted":accepted,"pending":pending,"rejected":rejected,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_integrated_at":now(),"accepted_count":len(accepted),
      "pending_count":len(pending),"rejected_count":len(rejected)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"accepted_count":len(accepted)})
    return {"success":True,"status":"specialist_insight_integration_complete","report":report}

def status():
    return {"success":True,"status":"specialist_insight_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"insights":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=integrate() if a=="integrate" else status() if a=="status" else {"success":False,"allowed":["integrate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
