#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"reliability_config.json"; OUT=M/"reliability_report.json"
STATE=M/"reliability_state.json"; HEALTH=M/"reliability_health.json"

SOURCES=[
 ("control_cycle",M/"control_cycle_health.json",25),
 ("cycle_supervisor",M/"cycle_supervisor_health.json",20),
 ("incident_escalation",M/"incident_escalation_health.json",25),
 ("exception_recovery",M/"exception_recovery_state.json",15),
 ("readiness",M/"readiness_report.json",15)
]

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def now():return datetime.now(timezone.utc).isoformat()

def run():
    cfg=load(CFG,{})
    score=0; checks=[]
    for name,p,weight in SOURCES:
        d=load(p,{})
        if name=="readiness": ok=d.get("ready",True)
        else: ok=d.get("healthy", d.get("cycle_success", d.get("recovery_attempted") is not True))
        ok=bool(ok)
        if ok: score+=weight
        checks.append({"component":name,"healthy":ok,"weight":weight,"source_exists":p.exists()})
    status="healthy" if score>=cfg.get("minimum_healthy_score",70) else "degraded"
    if score<cfg.get("critical_score",40): status="critical"
    report={"generated_at":now(),"reliability_score":score,"status":status,"checks":checks,
            "automatic_external_write":False,"automatic_code_changes":False,
            "automatic_merge":False,"automatic_deploy":False,
            "automatic_spending":False,"automatic_destructive_actions":False}
    save(OUT,report)
    save(STATE,{"last_scored_at":now(),"reliability_score":score,"status":status})
    save(HEALTH,{"healthy":status=="healthy","last_checked_at":now(),"score":score,"status":status})
    return {"success":True,"status":"reliability_score_complete","report":report}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="run":r=run()
elif a=="status":r={"success":True,"status":"reliability_status",
                    "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(OUT,{})}
else:r={"success":False,"status":"unknown_action","allowed":["run","status"]}
print(json.dumps(r,indent=2))
