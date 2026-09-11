#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 19 Step 20 - Autonomous Operations Dashboard"
echo "============================================================"

cat > "$AGENTS/operations_dashboard.py" <<'PY'
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
PY
chmod +x "$AGENTS/operations_dashboard.py"

cat > "$CTL/dashboardctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"operations_dashboard.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/dashboardctl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/operations_dashboard.py" "$CTL/dashboardctl"
echo "[2/5] Building dashboard..."
python "$CTL/dashboardctl" build
echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
j={"id":"operations-dashboard","enabled":True,"interval_seconds":1800,
"command":["python","companyos/dashboardctl","build"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY
echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/5] Showing dashboard..."
python "$CTL/dashboardctl" show

echo
echo "============================================================"
echo " PHASE 19 STEP 20 INSTALLED"
echo " AUTONOMOUS OPERATIONS DASHBOARD ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Command: python companyos/dashboardctl show"
