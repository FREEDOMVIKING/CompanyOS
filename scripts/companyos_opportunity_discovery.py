#!/usr/bin/env python3
import json, os, sys, time, hashlib
from pathlib import Path
ROOT=Path.home()/"companyos"
RT=ROOT/".companyos_runtime"
OUT=RT/"opportunities"
OUT.mkdir(parents=True,exist_ok=True)
CAND=OUT/"candidates.json"
SCORED=OUT/"scored_opportunities.json"
STATE=OUT/"discovery_state.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,x):
    p.write_text(json.dumps(x,indent=2,sort_keys=True))

def norm(s): return " ".join(str(s).lower().split())
def oid(x):
    key=norm(x.get("title",""))+"|"+norm(x.get("market",""))+"|"+norm(x.get("model",""))
    return hashlib.sha256(key.encode()).hexdigest()[:16]

def score(x):
    # Evidence-first deterministic scoring. Unknowns do not receive invented positive scores.
    demand=float(x.get("demand_evidence",0))
    margin=float(x.get("margin_potential",0))
    speed=float(x.get("speed_to_revenue",0))
    fit=float(x.get("capability_fit",0))
    defens=float(x.get("defensibility",0))
    risk=float(x.get("execution_risk",5))
    capital=float(x.get("capital_intensity",5))
    evidence=float(x.get("evidence_quality",0))
    total=(demand*0.22+margin*0.18+speed*0.16+fit*0.16+defens*0.08+
           evidence*0.20-risk*0.12-capital*0.08)
    return round(max(0,min(10,total)),3)

def discover():
    existing=load(CAND,[])
    inbox=RT/"ceo_opportunity_inbox"
    gathered=list(existing)
    if inbox.exists():
        for f in sorted(inbox.glob("*.json")):
            d=load(f,{})
            if isinstance(d,dict):
                d.setdefault("source",str(f))
                gathered.append(d)
    seen={}; dup=0
    for x in gathered:
        if not isinstance(x,dict): continue
        x=dict(x); x["opportunity_id"]=x.get("opportunity_id") or oid(x)
        k=oid(x)
        if k in seen: dup+=1; continue
        seen[k]=x
    vals=list(seen.values())
    save(CAND,vals)
    return vals,dup

def rank():
    vals,dup=discover()
    out=[]
    for x in vals:
        y=dict(x); y["score"]=score(y)
        y["qualified"]=bool(y["score"]>=float(os.getenv("COMPANYOS_OPPORTUNITY_MIN_SCORE","5.5"))
                            and float(y.get("evidence_quality",0))>=3)
        out.append(y)
    out.sort(key=lambda z:(z["qualified"],z["score"]),reverse=True)
    save(SCORED,out)
    st={"ok":True,"ts":time.time(),"candidates":len(out),"duplicates_suppressed":dup,
        "qualified":sum(1 for x in out if x["qualified"]),
        "top":[{"opportunity_id":x["opportunity_id"],"title":x.get("title"),"score":x["score"]} for x in out[:10]]}
    save(STATE,st); return st

def submit_sample():
    # Controlled test only; never auto-launches or performs external actions.
    a=load(CAND,[])
    a.append({"title":"CompanyOS Opportunity Engine Test","market":"internal-test","model":"test",
      "demand_evidence":7,"margin_potential":7,"speed_to_revenue":8,"capability_fit":9,
      "defensibility":5,"execution_risk":2,"capital_intensity":1,"evidence_quality":8,
      "auto_launch":False,"approval_required_for_external_actions":True})
    save(CAND,a); return rank()

cmd=sys.argv[1] if len(sys.argv)>1 else "status"
if cmd in ("discover","rank","cycle"): r=rank()
elif cmd=="test": r=submit_sample()
elif cmd=="status": r=load(STATE,{"ok":True,"status":"not_run"})
else: raise SystemExit("usage: companyos_opportunity_discovery.py [discover|rank|cycle|test|status]")
print(json.dumps(r,indent=2))
