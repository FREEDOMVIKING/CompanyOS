#!/usr/bin/env python3
import json,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"validated_insight_refresh_config.json"
SOURCE=MEM/"specialist_work_results.json"
TARGET=MEM/"validated_insights.json"
STATE=MEM/"validated_insight_refresh_state.json"
REPORT=MEM/"validated_insight_refresh_report.json"
HEALTH=MEM/"validated_insight_refresh_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2),encoding="utf-8"); t.replace(p)
def f(v,d=0):
    try:return float(v)
    except:return float(d)
def ident(row):
    raw="|".join(str(row.get(k,"")) for k in ("result_id","work_id","opportunity_id"))
    return "insight-"+hashlib.sha256(raw.encode()).hexdigest()[:20]

def refresh():
    cfg=load(CFG,{})
    rows=load(SOURCE,{}).get("results",[])
    doc=load(TARGET,{"insights":[]})
    insights=doc.get("insights",[])
    seen={x.get("source_result_id") for x in insights if x.get("source_result_id")}
    minimum=f(cfg.get("minimum_confidence",.5),.5)
    maximum=int(cfg.get("maximum_results_per_cycle",50))
    added=[];rejected=[]
    for row in rows:
        if len(added)>=maximum: break
        if row.get("status")!="completed": continue
        rid=row.get("result_id") or row.get("work_id")
        if not rid or rid in seen: continue
        actual=row.get("actual_result")
        if not isinstance(actual,dict):
            rejected.append({"source_result_id":rid,"reason":"missing_structured_result"}); continue
        confidence=f(actual.get("confidence",0),0)
        if confidence<minimum:
            rejected.append({"source_result_id":rid,"reason":"confidence_below_threshold","confidence":confidence}); continue
        insight={
          "insight_id":ident(row),
          "source_result_id":rid,
          "work_id":row.get("work_id"),
          "plan_id":row.get("plan_id"),
          "decision_id":row.get("decision_id"),
          "opportunity_id":row.get("opportunity_id"),
          "summary":actual.get("summary"),
          "findings":actual.get("findings",[]),
          "recommendations":actual.get("recommendations",[]),
          "risks":actual.get("risks",[]),
          "next_internal_actions":actual.get("next_internal_actions",[]),
          "confidence":confidence,
          "validation_status":"validated_for_internal_reasoning",
          "execution_boundary":"internal_non_destructive_only",
          "validated_at":now()
        }
        insights.append(insight);added.append(insight);seen.add(rid)
    save(TARGET,{"generated_at":now(),"insight_count":len(insights),"insights":insights})
    report={"generated_at":now(),"added_count":len(added),"rejected_count":len(rejected),
      "total_insight_count":len(insights),"added":added,"rejected":rejected,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_refresh_at":now(),"added_count":len(added),"total_insight_count":len(insights)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"total_insight_count":len(insights)})
    return {"success":True,"status":"validated_insight_refresh_complete","report":report}

def status():
    return {"success":True,"status":"validated_insight_refresh_status",
      "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=refresh() if a=="refresh" else status() if a=="status" else {"success":False,"allowed":["refresh","status"]}
print(json.dumps(r,indent=2)); raise SystemExit(0 if r.get("success") else 1)
