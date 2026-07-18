#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"portfolio_performance_config.json"
PORT=MEM/"rebalanced_opportunity_portfolio.json"
OUTCOMES=MEM/"opportunity_action_scores.json"
STATE=MEM/"portfolio_performance_state.json"
REPORT=MEM/"portfolio_performance_report.json"
HEALTH=MEM/"portfolio_performance_health.json"
PRIORITIES=MEM/"portfolio_resource_priorities.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def num(v,d=0):
    try:return float(v)
    except:return float(d)

def evaluate():
    cfg=load(CFG,{})
    rows=load(PORT,{}).get("opportunities",[])
    action_scores=load(OUTCOMES,{}).get("actions",{})
    minimum=num(cfg.get("minimum_score_for_resource_priority",60))
    min_samples=int(cfg.get("minimum_learning_samples",2))
    maximum=int(cfg.get("maximum_priority_candidates",5))
    ranked=[]

    for row in rows:
        oid=str(row.get("id") or "")
        related=[v for k,v in action_scores.items() if oid and k.startswith(oid+"-")]
        samples=sum(int(x.get("samples",0) or 0) for x in related)
        learned=(sum(num(x.get("score",50),50) for x in related)/len(related)) if related else 50.0
        strategic=num(row.get("final_opportunity_score",0))
        readiness=round((strategic*.7)+(learned*.3),2) if samples>=min_samples else round(strategic,2)
        ranked.append({
          "id":row.get("id"),"title":row.get("title"),"category":row.get("category"),
          "strategic_score":round(strategic,2),"learned_score":round(learned,2),
          "learning_samples":samples,"resource_readiness_score":readiness,
          "priority_eligible":readiness>=minimum,
          "recommendation":"prioritize_internal_resources" if readiness>=minimum else "observe"
        })

    ranked.sort(key=lambda x:(x["resource_readiness_score"],x["learning_samples"]),reverse=True)
    priority=[x for x in ranked if x["priority_eligible"]][:maximum]
    save(PRIORITIES,{"generated_at":now(),"candidates":priority,
      "note":"Internal prioritization only; no spending or fund movement is authorized."})

    report={"generated_at":now(),"evaluated_count":len(ranked),"priority_count":len(priority),
      "ranked":ranked,"priority_candidates":priority,
      "automatic_external_write":False,"automatic_customer_contact":False,
      "automatic_publication":False,"automatic_spending":False,"automatic_fund_transfer":False,
      "automatic_code_changes":False,"automatic_merge":False,"automatic_deploy":False,
      "automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_evaluated_at":now(),"evaluated_count":len(ranked),"priority_count":len(priority),
      "top_candidate":priority[0]["title"] if priority else None})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"evaluated_count":len(ranked)})
    return {"success":True,"status":"portfolio_performance_evaluation_complete","report":report}

def status():
    return {"success":True,"status":"portfolio_performance_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"priorities":load(PRIORITIES,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=evaluate() if a=="evaluate" else status() if a=="status" else {"success":False,"allowed":["evaluate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
