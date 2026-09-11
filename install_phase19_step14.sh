#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 19 Step 14 - Autonomous Incident Escalation Engine"
echo "============================================================"

cat > "$MEM/incident_escalation_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_incident_detection": true,
  "automatic_internal_containment": true,
  "critical_failure_threshold": 3,
  "halt_on_critical_incident": true,
  "automatic_external_write": false,
  "automatic_code_changes": false,
  "automatic_deploy": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/incident_escalation_engine.py" <<'PY'
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
PY
chmod +x "$AGENTS/incident_escalation_engine.py"

cat > "$CTL/incidentctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"incident_escalation_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/incidentctl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/incident_escalation_engine.py" "$CTL/incidentctl"
echo "[2/5] Running incident scan..."
python "$CTL/incidentctl" run
echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
j={"id":"incident-escalation","enabled":True,"interval_seconds":1800,
   "command":["python","companyos/incidentctl","run"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY
echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/5] Status..."
python "$CTL/incidentctl" status

echo
echo "============================================================"
echo " PHASE 19 STEP 14 INSTALLED"
echo " AUTONOMOUS INCIDENT ESCALATION ENGINE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/incidentctl run"
echo "  python companyos/incidentctl status"
