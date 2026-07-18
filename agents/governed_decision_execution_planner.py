#!/usr/bin/env python3
import json,sys,re
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"governed_execution_plan_config.json"
DECISIONS=MEM/"governed_ceo_decisions.json"
STATE=MEM/"governed_execution_plan_state.json"
REPORT=MEM/"governed_execution_plan_report.json"
HEALTH=MEM/"governed_execution_plan_health.json"
OUT=MEM/"governed_internal_execution_plans.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def classify(text):
    s=str(text or "").lower()
    rules=[
      ("research",r"\bresearch\b|\binvestigat|\bmarket\b"),
      ("review",r"\breview\b|\baudit\b|\bcheck\b|\bvalidate\b"),
      ("prioritize",r"\bpriorit|\brank\b|\bscore\b"),
      ("coordinate",r"\bcoordinat|\bdelegat|\bassign\b"),
      ("plan",r"\bplan\b|\bstrateg|\broadmap\b"),
    ]
    for kind,pat in rules:
        if re.search(pat,s): return kind
    return "analyze"

def build():
    cfg=load(CFG,{})
    approved=load(DECISIONS,{}).get("approved",[])
    maximum=int(cfg.get("maximum_plans_per_cycle",10))
    allowed_auth=set(cfg.get("allowed_authority",[]))
    allowed_actions=set(cfg.get("allowed_action_types",[]))
    plans=[];held=[]

    for decision in approved[:maximum]:
        authority=decision.get("execution_authority")
        if authority not in allowed_auth:
            held.append({"decision_id":decision.get("decision_id"),"reason":"authority_not_allowed"})
            continue

        proposed=decision.get("proposed_internal_actions",[]) or []
        if not proposed:
            proposed=["Analyze the governed decision and prepare the next internal plan."]

        steps=[]
        for i,action in enumerate(proposed,1):
            action_type=classify(action)
            if action_type not in allowed_actions:
                continue
            steps.append({
              "step":i,"action_type":action_type,"instruction":str(action),
              "authority":"internal_non_destructive_only","status":"planned"
            })

        if not steps:
            held.append({"decision_id":decision.get("decision_id"),"reason":"no_allowed_internal_steps"})
            continue

        plans.append({
          "plan_id":f"{decision.get('decision_id')}-plan",
          "decision_id":decision.get("decision_id"),
          "opportunity_id":decision.get("opportunity_id"),
          "title":decision.get("title"),
          "recommended_direction":decision.get("recommended_direction"),
          "confidence":decision.get("confidence"),
          "execution_authority":"internal_non_destructive_only",
          "steps":steps,"status":"ready_for_internal_execution_queue",
          "created_at":now()
        })

    payload={"generated_at":now(),"plan_count":len(plans),"plans":plans,
      "note":"Plans contain internal non-destructive work only and grant no external authority."}
    save(OUT,payload)
    report={"generated_at":now(),"plan_count":len(plans),"held_count":len(held),
      "plans":plans,"held":held,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_planned_at":now(),"plan_count":len(plans),"held_count":len(held)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"plan_count":len(plans)})
    return {"success":True,"status":"governed_execution_planning_complete","report":report}

def status():
    return {"success":True,"status":"governed_execution_plan_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"plans":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="plan" else status() if a=="status" else {"success":False,"allowed":["plan","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
