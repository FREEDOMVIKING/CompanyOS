#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_config.json"; SIGNALS=MEM/"business_signals.json"
OUT=MEM/"generated_business_opportunities.json"; STATE=MEM/"opportunity_generation_state.json"; HEALTH=MEM/"opportunity_generation_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def oid(title,source):return hashlib.sha256(f"{title}|{source}".encode()).hexdigest()[:16]

def generate():
    cfg=load(CFG,{})
    rows=load(SIGNALS,{}).get("signals",[])
    out=[]
    for s in rows:
        typ=s.get("type")
        data=s.get("data",{})
        strength=float(s.get("strength",50) or 50)
        title=None; category="general"; reason=""
        if typ=="priority_opportunity":
            title=data.get("title") or "Advance high-priority business opportunity"
            category=data.get("category") or "growth"
            reason="High internal readiness score"
        elif typ=="forecast":
            title="Review forecast-driven growth or risk actions"
            category="strategy"; reason="Forecast signal available"
        elif typ=="finance":
            title="Improve cash flow, margin, or receivable performance"
            category="finance"; reason="Financial signal available"
        elif typ=="crm":
            title="Advance customer pipeline and retention opportunities"
            category="sales"; reason="CRM signal available"
        elif typ=="outcomes":
            title="Scale actions with strongest measured outcomes"
            category="optimization"; reason="Outcome feedback available"
        if not title: continue
        out.append({"id":oid(title,s.get("source")),"title":title,"category":category,
          "score":round(strength,2),"reason":reason,"source":s.get("source"),
          "status":"generated_internal_candidate","generated_at":now()})
    dedup={x["id"]:x for x in out}
    rows=list(dedup.values())
    rows=[x for x in rows if x["score"]>=float(cfg.get("minimum_opportunity_score",45))]
    rows=sorted(rows,key=lambda x:x["score"],reverse=True)[:int(cfg.get("maximum_generated_opportunities",20))]
    payload={"generated_at":now(),"opportunity_count":len(rows),"opportunities":rows}
    save(OUT,payload);save(STATE,{"last_generated_at":now(),"opportunity_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"opportunity_count":len(rows)})
    return {"success":True,"status":"business_opportunity_generation_complete","report":payload}

def status():
    return {"success":True,"status":"business_opportunity_generation_status",
      "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=generate() if a=="generate" else status() if a=="status" else {"success":False,"allowed":["generate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
