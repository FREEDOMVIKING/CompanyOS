#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"execution_readiness_report.json"; STATE=MEM/"execution_readiness_state.json"; HEALTH=MEM/"execution_readiness_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(n,d):
    try:return json.loads((MEM/n).read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run():
    projects=load("project_execution_registry.json",{}).get("projects",[])
    risks=load("enterprise_risk_register.json",{}).get("risk_count",0)
    approvals=load("governed_approval_queue.json",{}).get("items",[])
    pending=sum(1 for x in approvals if x.get("status")=="pending")
    rows=[]
    for p in projects:
        score=float(p.get("validation_score",50) or 50)
        if risks: score=max(0,score-min(20,risks*0.25))
        if pending: score=max(0,score-5)
        rows.append({"project_id":p.get("project_id"),"title":p.get("title"),
                     "readiness_score":round(score,2),
                     "status":"internally_ready" if score>=60 else "needs_more_preparation",
                     "external_execution_authorized":False})
    payload={"generated_at":now(),"project_count":len(rows),"projects":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"project_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"execution_readiness_complete","report":payload}
def status():return {"success":True,"status":"execution_readiness_status","state":load("execution_readiness_state.json",{}),"health":load("execution_readiness_health.json",{})}
a=sys.argv[1] if len(sys.argv)>1 else "status";r=run() if a=="run" else status();print(json.dumps(r,indent=2))
