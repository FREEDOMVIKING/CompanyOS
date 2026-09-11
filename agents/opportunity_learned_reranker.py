#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"opportunity_rerank_config.json"
ALIGN=MEM/"strategic_alignment_report.json"
SCORES=MEM/"opportunity_action_scores.json"
REPORT=MEM/"opportunity_rerank_report.json"
STATE=MEM/"opportunity_rerank_state.json"
HEALTH=MEM/"opportunity_rerank_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2),encoding="utf-8"); t.replace(p)
def clamp(v): return max(0.0,min(100.0,v))

def rerank():
    cfg=load(CFG,{})
    aligned=load(ALIGN,{}).get("aligned_opportunities",[])
    scores=load(SCORES,{}).get("actions",{})
    aw=float(cfg.get("alignment_weight",.70)); lw=float(cfg.get("learned_outcome_weight",.30))
    total=aw+lw or 1.0
    minimum=int(cfg.get("minimum_learning_samples",2))
    maximum=int(cfg.get("maximum_opportunities",20))
    rows=[]

    for opp in aligned[:maximum]:
        oid=str(opp.get("id") or "")
        base=float(opp.get("alignment_score",50))
        related=[v for k,v in scores.items() if oid and k.startswith(oid+"-")]
        learned=50.0; samples=0
        if related:
            samples=sum(int(x.get("samples",0)) for x in related)
            vals=[float(x.get("score",50)) for x in related]
            learned=sum(vals)/len(vals)
        active=samples>=minimum
        final=((base*aw)+(learned*lw))/total if active else base
        rows.append({
          "id":opp.get("id"),"title":opp.get("title"),"category":opp.get("category"),
          "alignment_score":round(base,2),"learned_outcome_score":round(learned,2),
          "learning_samples":samples,"learning_active":active,
          "final_opportunity_score":round(clamp(final),2),
          "source":opp.get("source"),"recommendation":opp.get("recommendation")
        })

    rows.sort(key=lambda x:(x["final_opportunity_score"],x["learning_samples"]),reverse=True)
    for i,x in enumerate(rows,1): x["rank"]=i
    report={"generated_at":now(),"reranked_opportunities":rows,
            "top_opportunity":rows[0]["title"] if rows else None,
            "automatic_external_write":False,"automatic_customer_contact":False,
            "automatic_publication":False,"automatic_spending":False,
            "automatic_code_changes":False,"automatic_merge":False,
            "automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_reranked_at":now(),"opportunity_count":len(rows),
                "top_opportunity":report["top_opportunity"]})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"opportunity_count":len(rows)})
    return {"success":True,"status":"learned_opportunity_reranking_complete","report":report}

def status():
    return {"success":True,"status":"opportunity_rerank_status","state":load(STATE,{}),
            "health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=rerank() if a=="rerank" else status() if a=="status" else {"success":False,"allowed":["rerank","status"]}
print(json.dumps(r,indent=2)); raise SystemExit(0 if r.get("success") else 1)
