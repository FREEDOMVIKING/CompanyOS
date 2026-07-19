#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_config.json"
OPS=MEM/"generated_business_opportunities.json"
INSIGHTS=MEM/"validated_insights.json"
OUT=MEM/"validated_business_opportunities.json"
STATE=MEM/"opportunity_validation_state.json"
HEALTH=MEM/"opportunity_validation_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def validate():
    cfg=load(CFG,{})
    ops=load(OPS,{}).get("opportunities",[])
    insights=load(INSIGHTS,{}).get("insights",[])
    minimum=float(cfg.get("minimum_validation_score",55))
    rows=[]
    for o in ops:
        base=float(o.get("score",50) or 50)
        related=[i for i in insights if i.get("opportunity_id") in (o.get("id"),o.get("opportunity_id"))]
        confidence=(sum(float(i.get("confidence",0) or 0) for i in related)/len(related)) if related else 0
        score=round(min(100,base+(confidence*20)),2)
        rows.append({
          **o,"validation_score":score,"supporting_insight_count":len(related),
          "validation_status":"validated_internal_candidate" if score>=minimum else "needs_more_evidence",
          "validated_at":now()
        })
    rows.sort(key=lambda x:x["validation_score"],reverse=True)
    payload={"generated_at":now(),"opportunity_count":len(rows),"opportunities":rows}
    save(OUT,payload);save(STATE,{"last_validated_at":now(),"opportunity_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"opportunity_count":len(rows)})
    return {"success":True,"status":"opportunity_validation_complete","report":payload}

def status():
    return {"success":True,"status":"opportunity_validation_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=validate() if a=="validate" else status() if a=="status" else {"success":False,"allowed":["validate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
