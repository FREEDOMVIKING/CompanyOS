#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"ceo_insight_decision_config.json"
INSIGHTS=MEM/"ceo_specialist_insights.json"
STATE=MEM/"ceo_insight_decision_state.json"
REPORT=MEM/"ceo_insight_decision_report.json"
HEALTH=MEM/"ceo_insight_decision_health.json"
OUT=MEM/"ceo_decision_candidates.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def num(v,d=0):
    try:return float(v)
    except:return float(d)

def synthesize():
    cfg=load(CFG,{})
    rows=load(INSIGHTS,{}).get("insights",[])
    maximum=int(cfg.get("maximum_decisions_per_cycle",10))
    minimum=num(cfg.get("minimum_confidence",.5))
    decisions=[];rejected=[]

    for row in rows:
        confidence=num(row.get("confidence",0))
        if confidence<minimum:
            rejected.append({"insight_id":row.get("insight_id"),"reason":"confidence_below_threshold"})
            continue
        recs=row.get("recommendations",[]) or []
        actions=row.get("next_internal_actions",[]) or []
        risks=row.get("risks",[]) or []
        decisions.append({
          "decision_id":f"{row.get('insight_id')}-decision",
          "opportunity_id":row.get("opportunity_id"),"title":row.get("title"),
          "source_insight_id":row.get("insight_id"),"confidence":confidence,
          "recommended_direction":recs[0] if recs else "continue_internal_analysis",
          "supporting_recommendations":recs,
          "known_risks":risks,
          "proposed_internal_actions":actions,
          "decision_class":"internal_candidate",
          "status":"ready_for_ceo_internal_review",
          "created_at":now()
        })
        if len(decisions)>=maximum:break

    payload={"generated_at":now(),"decision_count":len(decisions),"decisions":decisions,
      "note":"Decision candidates are internal recommendations only and grant no new execution authority."}
    save(OUT,payload)
    report={"generated_at":now(),"decision_count":len(decisions),"rejected_count":len(rejected),
      "decisions":decisions,"rejected":rejected,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_synthesized_at":now(),"decision_count":len(decisions),"rejected_count":len(rejected)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"decision_count":len(decisions)})
    return {"success":True,"status":"ceo_insight_decision_synthesis_complete","report":report}

def status():
    return {"success":True,"status":"ceo_insight_decision_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"decisions":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=synthesize() if a=="synthesize" else status() if a=="status" else {"success":False,"allowed":["synthesize","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
