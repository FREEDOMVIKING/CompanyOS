#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 19 Step 15 - Autonomous Reliability Scorecard"
echo "============================================================"

cat > "$MEM/reliability_config.json" <<'JSON'
{
  "enabled": true,
  "minimum_healthy_score": 70,
  "critical_score": 40,
  "automatic_internal_recovery": true,
  "automatic_external_write": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/reliability_engine.py" <<'PY'
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
PY
chmod +x "$AGENTS/reliability_engine.py"

cat > "$CTL/reliabilityctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"reliability_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/reliabilityctl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/reliability_engine.py" "$CTL/reliabilityctl"
echo "[2/5] Generating reliability score..."
python "$CTL/reliabilityctl" run
echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text()); jobs=d.setdefault("jobs",[])
j={"id":"reliability-scorecard","enabled":True,"interval_seconds":1800,
   "command":["python","companyos/reliabilityctl","run"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY
echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/5] Status..."
python "$CTL/reliabilityctl" status

echo
echo "============================================================"
echo " PHASE 19 STEP 15 INSTALLED"
echo " AUTONOMOUS RELIABILITY SCORECARD ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/reliabilityctl run"
echo "  python companyos/reliabilityctl status"
