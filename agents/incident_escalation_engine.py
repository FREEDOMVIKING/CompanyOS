#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"incident_escalation_config.json"; SUP=M/"cycle_supervisor_state.json"
CYCLE=M/"control_cycle_state.json"; READ=M/"readiness_report.json"
STATE=M/"incident_escalation_state.json"; REPORT=M/"incident_escalation_report.json"
HEALTH=M/"incident_escalation_health.json"; HALT=M/"HALT_AUTONOMY"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def now():return datetime.now(timezone.utc).isoformat()

def run():
    cfg=load(CFG,{})
    sup=load(SUP,{})
    cyc=load(CYCLE,{})
    readiness=load(READ,{})
    incidents=[]

    failures=int(sup.get("consecutive_failures",0))
    if failures>=int(cfg.get("critical_failure_threshold",3)):
        incidents.append({"severity":"critical","type":"repeated_control_cycle_failure","count":failures})

    if readiness and readiness.get("ready") is False:
        issues=readiness.get("issues",[])
        if issues:
            incidents.append({"severity":"warning","type":"system_readiness_degraded","issues":issues})

    if cyc.get("cycle_success") is False:
        incidents.append({"severity":"warning","type":"latest_control_cycle_failed"})

    critical=any(x["severity"]=="critical" for x in incidents)
    halted=False
    if critical and cfg.get("halt_on_critical_incident",True):
        HALT.write_text("Critical incident containment activated at "+now()+"\n")
        halted=True

    report={"generated_at":now(),"incident_count":len(incidents),"incidents":incidents,
            "critical_incident":critical,"autonomy_halted":halted or HALT.exists(),
            "automatic_external_write":False,"automatic_code_changes":False,
            "automatic_deploy":False,"automatic_spending":False,
            "automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_scan_at":now(),"incident_count":len(incidents),
                "critical_incident":critical,"autonomy_halted":report["autonomy_halted"]})
    save(HEALTH,{"healthy":not critical,"last_checked_at":now(),
                 "incident_count":len(incidents)})
    return {"success":True,"status":"incident_scan_complete","report":report}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="run":r=run()
elif a=="status":r={"success":True,"status":"incident_escalation_status",
                    "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(REPORT,{})}
else:r={"success":False,"status":"unknown_action","allowed":["run","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
