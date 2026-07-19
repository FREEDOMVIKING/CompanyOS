#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle5_config.json"; SIGNALS=MEM/"business_signals.json"
OPS=MEM/"generated_business_opportunities.json"; OUT=MEM/"market_intelligence_report.json"
STATE=MEM/"market_intelligence_state.json"; HEALTH=MEM/"market_intelligence_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def sid(x):return hashlib.sha256(str(x).encode()).hexdigest()[:16]
def run():
    cfg=load(CFG,{})
    rows=[]
    for s in load(SIGNALS,{}).get("signals",[]):
        rows.append({"signal_id":sid(s),"type":s.get("type"),"strength":s.get("strength",50),
                     "source":s.get("source"),"status":"internal_market_signal"})
    for o in load(OPS,{}).get("opportunities",[]):
        rows.append({"signal_id":sid(o.get("id") or o.get("title")),"type":"opportunity",
                     "strength":o.get("score",50),"source":o.get("source"),
                     "title":o.get("title"),"status":"internal_market_signal"})
    rows=sorted(rows,key=lambda x:float(x.get("strength",0) or 0),reverse=True)[:int(cfg.get("maximum_market_signals",50))]
    payload={"generated_at":now(),"signal_count":len(rows),"signals":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"signal_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"signal_count":len(rows)})
    return {"success":True,"status":"market_intelligence_complete","report":payload}
def status():return {"success":True,"status":"market_intelligence_status","state":load(STATE,{}),"health":load(HEALTH,{})}
a=sys.argv[1] if len(sys.argv)>1 else "status";r=run() if a=="run" else status()
print(json.dumps(r,indent=2))
