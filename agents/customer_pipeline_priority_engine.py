#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle5_config.json"; OUT=MEM/"customer_pipeline_priorities.json"
STATE=MEM/"customer_pipeline_priority_state.json"; HEALTH=MEM/"customer_pipeline_priority_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(n,d):
    try:return json.loads((MEM/n).read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def pid(x):return hashlib.sha256(str(x).encode()).hexdigest()[:16]
def run():
    cfg=load("phase24_bundle5_config.json",{})
    sources=[]
    for name in ["sales_pipeline.json","crm_state.json","generated_business_opportunities.json"]:
        d=load(name,{})
        if name=="generated_business_opportunities.json":
            for o in d.get("opportunities",[]): sources.append({"title":o.get("title"),"score":o.get("score",50),"source":name})
        elif isinstance(d,dict):
            for k in ("leads","opportunities","items","pipeline"):
                v=d.get(k,[])
                if isinstance(v,list):
                    for x in v:
                        if isinstance(x,dict): sources.append({"title":x.get("title") or x.get("name") or "Pipeline item","score":x.get("score",50),"source":name})
    rows=[{"priority_id":pid(x),"title":x["title"],"priority_score":float(x.get("score",50) or 50),
           "source":x["source"],"status":"internal_priority_only","customer_contact_authorized":False} for x in sources]
    rows=sorted(rows,key=lambda x:x["priority_score"],reverse=True)[:int(cfg.get("maximum_customer_priorities",25))]
    payload={"generated_at":now(),"priority_count":len(rows),"priorities":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"priority_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"customer_pipeline_priority_complete","report":payload}
def status():return {"success":True,"status":"customer_pipeline_priority_status","state":load("customer_pipeline_priority_state.json",{}),"health":load("customer_pipeline_priority_health.json",{})}
a=sys.argv[1] if len(sys.argv)>1 else "status";r=run() if a=="run" else status();print(json.dumps(r,indent=2))
