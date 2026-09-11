#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
OUT=M/"operations_dashboard.json"
SOURCES={
 "control_cycle":"control_cycle_state.json",
 "supervisor":"cycle_supervisor_state.json",
 "incidents":"incident_escalation_state.json",
 "reliability":"reliability_state.json",
 "resources":"resource_monitor_report.json",
 "watchdog":"watchdog_state.json",
 "backup":"state_backup_state.json",
 "github":"github_intelligence_state.json",
 "preflight":"preflight_gate_report.json",
 "drift":"drift_report.json"
}
def load(p):
    try:return json.loads(p.read_text())
    except:return {}
def build():
    data={k:load(M/v) for k,v in SOURCES.items()}
    score=data["reliability"].get("reliability_score")
    critical=data["incidents"].get("critical_incident",False)
    stale=data["watchdog"].get("heartbeat_stale",False)
    overall="critical" if critical else "degraded" if stale or (score is not None and score<70) else "healthy"
    out={"generated_at":datetime.now(timezone.utc).isoformat(),"overall_status":overall,
         "reliability_score":score,"systems":data}
    t=OUT.with_suffix(".json.tmp");t.write_text(json.dumps(out,indent=2));t.replace(OUT)
    return {"success":True,"status":"operations_dashboard_generated","dashboard":out}
a=sys.argv[1] if len(sys.argv)>1 else "show"
r=build() if a=="build" else {"success":True,"status":"operations_dashboard","dashboard":load(OUT)} if a=="show" else {"success":False}
print(json.dumps(r,indent=2))
