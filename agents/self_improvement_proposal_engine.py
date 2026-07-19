#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_config.json"; OUT=MEM/"self_improvement_proposals.json"
STATE=MEM/"self_improvement_proposal_state.json"; HEALTH=MEM/"self_improvement_proposal_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def pid(text):return hashlib.sha256(text.encode()).hexdigest()[:16]

def propose():
    cfg=load("phase23_config.json",{})
    perf=load("business_performance_scorecard.json",{})
    autonomy=load("autonomy_core_report.json",{})
    usage=load("api_usage_state.json",{})
    proposals=[]

    if float(perf.get("overall_score",100) or 100)<75:
        proposals.append(("Improve low-scoring business performance dimensions",80,"performance"))
    failed=autonomy.get("failed_steps",[]) or []
    if failed:
        proposals.append((f"Investigate repeated autonomy failures: {', '.join(failed[:5])}",95,"reliability"))
    if int(usage.get("requests",0) or 0)>100:
        proposals.append(("Reduce unnecessary AI calls using stronger deduplication and batching",75,"efficiency"))
    proposals.append(("Review high-value repeated manual workflows for safe internal automation",65,"automation"))
    proposals.append(("Improve specialist prompt quality using measured result confidence and outcomes",70,"ai_quality"))

    rows=[{"id":pid(t),"title":t,"priority":p,"category":c,
      "status":"proposal_only_requires_governed_review","generated_at":now()} for t,p,c in proposals]
    rows=sorted(rows,key=lambda x:x["priority"],reverse=True)[:int(cfg.get("maximum_improvement_proposals",20))]
    payload={"generated_at":now(),"proposal_count":len(rows),"proposals":rows,
      "automatic_code_changes":False,"automatic_merge":False,"automatic_deploy":False}
    save(OUT,payload);save(STATE,{"last_generated_at":now(),"proposal_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"proposal_count":len(rows)})
    return {"success":True,"status":"self_improvement_proposals_complete","report":payload}

def status():
    return {"success":True,"status":"self_improvement_proposal_status",
      "state":load("self_improvement_proposal_state.json",{}),"health":load("self_improvement_proposal_health.json",{}),
      "report":load("self_improvement_proposals.json",{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=propose() if a=="propose" else status() if a=="status" else {"success":False,"allowed":["propose","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
