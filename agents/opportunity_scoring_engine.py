#!/usr/bin/env python3
import json, hashlib
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase25_bundle3_config.json"; OUT=MEM/"scored_opportunities.json"; STATE=MEM/"opportunity_scoring_state.json"; HEALTH=MEM/"opportunity_scoring_health.json"
SOURCES=[MEM/"generated_business_opportunities.json",MEM/"opportunity_discovery_results.json",MEM/"business_opportunities.json"]
def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def fid(x): return hashlib.sha256(str(x).encode()).hexdigest()[:18]
def num(v,d=50):
    try:return float(v)
    except:return float(d)
def collect():
    rows=[]
    for p in SOURCES:
        d=load(p,{})
        if isinstance(d,list): vals=d
        else:
            vals=[]
            for k in ("opportunities","results","items"):
                if isinstance(d.get(k),list): vals.extend(d[k])
        rows.extend(x for x in vals if isinstance(x,dict))
    dedup={}
    for x in rows: dedup[str(x.get("id") or x.get("opportunity_id") or x.get("title") or fid(x))]=x
    return list(dedup.values())
def run():
    cfg=load(CFG,{})
    out=[]
    for o in collect()[:int(cfg.get("maximum_opportunities",25))]:
        upside=num(o.get("upside",o.get("score",60)),60)
        conf=num(o.get("confidence",60),60); conf=conf*100 if conf<=1 else conf
        urgency=num(o.get("urgency",55),55); fit=num(o.get("strategic_fit",65),65); cost=num(o.get("cost_efficiency",60),60); risk=num(o.get("risk",40),40)
        score=upside*.30+conf*.20+urgency*.15+fit*.15+cost*.10+(100-risk)*.10
        out.append({"opportunity_id":o.get("id") or o.get("opportunity_id") or fid(o),"title":o.get("title","Untitled opportunity"),"category":o.get("category","general"),"score":round(score,2),"confidence":round(conf,2),"risk":round(risk,2),"status":"qualified_internal_candidate" if score>=cfg.get("minimum_opportunity_score",50) else "below_internal_threshold","source":o.get("source","internal"),"execution_boundary":"internal_non_destructive_only"})
    out.sort(key=lambda x:x["score"],reverse=True)
    payload={"generated_at":now(),"opportunity_count":len(out),"opportunities":out}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"opportunity_count":len(out)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"opportunity_scoring_complete","report":payload}
print(json.dumps(run(),indent=2))
