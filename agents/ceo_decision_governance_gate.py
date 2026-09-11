#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"ceo_decision_governance_config.json"
DECISIONS=MEM/"ceo_decision_candidates.json"
STATE=MEM/"ceo_decision_governance_state.json"
REPORT=MEM/"ceo_decision_governance_report.json"
HEALTH=MEM/"ceo_decision_governance_health.json"
OUT=MEM/"governed_ceo_decisions.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def num(v,d=0):
    try:return float(v)
    except:return float(d)

def govern():
    cfg=load(CFG,{})
    rows=load(DECISIONS,{}).get("decisions",[])
    maximum=int(cfg.get("maximum_decisions_per_cycle",10))
    minimum=num(cfg.get("minimum_confidence",.5))
    allowed=set(cfg.get("allowed_automatic_classes",["internal_candidate"]))
    approved=[];held=[]

    for row in rows[:maximum]:
        reasons=[]
        if num(row.get("confidence",0))<minimum: reasons.append("confidence_below_threshold")
        if row.get("decision_class") not in allowed: reasons.append("decision_class_not_automatic")
        if reasons:
            held.append({**row,"governance_status":"held","hold_reasons":reasons})
        else:
            approved.append({**row,"governance_status":"approved_internal_only",
              "execution_authority":"internal_non_destructive_only","governed_at":now()})

    payload={"generated_at":now(),"approved_count":len(approved),"held_count":len(held),
      "approved":approved,"held":held,
      "note":"Governance approval does not grant external, financial, deployment, publication, or destructive authority."}
    save(OUT,payload)
    report={"generated_at":now(),"approved_count":len(approved),"held_count":len(held),
      "approved":approved,"held":held,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_governed_at":now(),"approved_count":len(approved),"held_count":len(held)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"approved_count":len(approved)})
    return {"success":True,"status":"ceo_decision_governance_complete","report":report}

def status():
    return {"success":True,"status":"ceo_decision_governance_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"decisions":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=govern() if a=="govern" else status() if a=="status" else {"success":False,"allowed":["govern","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
