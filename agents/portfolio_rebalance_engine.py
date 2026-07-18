#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"portfolio_rebalance_config.json"
PORT=MEM/"active_opportunity_portfolio.json"
RERANK=MEM/"opportunity_rerank_report.json"
STATE=MEM/"portfolio_rebalance_state.json"; REPORT=MEM/"portfolio_rebalance_report.json"
HEALTH=MEM/"portfolio_rebalance_health.json"; OUT=MEM/"rebalanced_opportunity_portfolio.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def score(x):
    try:return float(x.get("final_opportunity_score",0) or 0)
    except:return 0.0

def rebalance():
    cfg=load(CFG,{})
    current=load(PORT,{}).get("opportunities",[])
    candidates=load(RERANK,{}).get("reranked_opportunities",[])
    max_active=int(cfg.get("maximum_active_opportunities",5))
    min_keep=float(cfg.get("minimum_keep_score",50))
    margin=float(cfg.get("replacement_margin",5))
    max_replace=int(cfg.get("maximum_replacements_per_cycle",2))

    kept=[dict(x) for x in current if score(x)>=min_keep]
    removed=[{"id":x.get("id"),"title":x.get("title"),"reason":"below_keep_score"} for x in current if score(x)<min_keep]
    active_ids={str(x.get("id")) for x in kept}
    pool=[dict(x) for x in candidates if str(x.get("id")) not in active_ids and score(x)>=min_keep]
    pool.sort(key=score,reverse=True); kept.sort(key=score,reverse=True)
    replacements=[]

    while len(kept)<max_active and pool:
        x=pool.pop(0);kept.append(x);active_ids.add(str(x.get("id")))
        replacements.append({"incoming":x.get("title"),"reason":"open_capacity"})

    for challenger in list(pool):
        if len(replacements)>=max_replace or not kept:break
        weakest=min(kept,key=score)
        if score(challenger)>=score(weakest)+margin:
            kept.remove(weakest);kept.append(challenger)
            replacements.append({"outgoing":weakest.get("title"),"incoming":challenger.get("title"),
                                  "score_improvement":round(score(challenger)-score(weakest),2),
                                  "reason":"materially_better_candidate"})

    kept.sort(key=score,reverse=True); kept=kept[:max_active]
    normalized=[]
    for i,x in enumerate(kept,1):
        normalized.append({"portfolio_rank":i,"id":x.get("id"),"title":x.get("title"),
          "category":x.get("category"),"final_opportunity_score":x.get("final_opportunity_score"),
          "learning_samples":x.get("learning_samples"),"learning_active":x.get("learning_active"),
          "status":"active_candidate"})
    out={"generated_at":now(),"active_count":len(normalized),"opportunities":normalized}
    save(OUT,out)
    report={"generated_at":now(),"active_count":len(normalized),"removed":removed,
            "replacements":replacements,"replacement_count":len(replacements),
            "automatic_external_write":False,"automatic_customer_contact":False,
            "automatic_publication":False,"automatic_spending":False,"automatic_code_changes":False,
            "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_rebalanced_at":now(),"active_count":len(normalized),
      "replacement_count":len(replacements)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"active_count":len(normalized)})
    return {"success":True,"status":"portfolio_rebalance_complete","report":report,"portfolio":out}

def status():
    return {"success":True,"status":"portfolio_rebalance_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"portfolio":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=rebalance() if a=="rebalance" else status() if a=="status" else {"success":False,"allowed":["rebalance","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
