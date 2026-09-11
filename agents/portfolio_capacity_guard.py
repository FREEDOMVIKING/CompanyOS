#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"portfolio_capacity_config.json"
PORT=MEM/"active_opportunity_portfolio.json"
STATE=MEM/"portfolio_capacity_state.json"
REPORT=MEM/"portfolio_capacity_report.json"
HEALTH=MEM/"portfolio_capacity_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def evaluate():
    cfg=load(CFG,{})
    portfolio=load(PORT,{"opportunities":[]})
    rows=portfolio.get("opportunities",[])
    max_active=int(cfg.get("maximum_active_opportunities",5))
    max_cat=int(cfg.get("maximum_per_category",2))
    min_score=float(cfg.get("minimum_final_score",50))
    accepted=[]; rejected=[]; counts=Counter()

    ordered=sorted(rows,key=lambda x:float(x.get("final_opportunity_score",0) or 0),reverse=True)
    for row in ordered:
        category=row.get("category") or "uncategorized"
        score=float(row.get("final_opportunity_score",0) or 0)
        reason=None
        if score < min_score: reason="below_minimum_score"
        elif len(accepted)>=max_active: reason="portfolio_capacity_reached"
        elif counts[category]>=max_cat: reason="category_concentration_limit"
        if reason:
            rejected.append({"id":row.get("id"),"title":row.get("title"),"reason":reason})
        else:
            accepted.append(row);counts[category]+=1

    report={
      "generated_at":now(),"input_count":len(rows),"accepted_count":len(accepted),
      "rejected_count":len(rejected),"category_counts":dict(counts),
      "accepted":accepted,"rejected":rejected,
      "automatic_external_write":False,"automatic_customer_contact":False,
      "automatic_publication":False,"automatic_spending":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False
    }
    save(REPORT,report)
    save(STATE,{"last_evaluated_at":now(),"accepted_count":len(accepted),
                "rejected_count":len(rejected),"category_counts":dict(counts)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"violations_prevented":len(rejected)})
    return {"success":True,"status":"portfolio_capacity_evaluation_complete","report":report}

def status():
    return {"success":True,"status":"portfolio_capacity_status","state":load(STATE,{}),
            "health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=evaluate() if a in ("evaluate","rebalance") else status() if a=="status" else {"success":False,"allowed":["evaluate","rebalance","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
