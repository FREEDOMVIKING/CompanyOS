#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase18_step19_$(date +%Y%m%d_%H%M%S)"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 18 Step 19 - Autonomous Dependency & Readiness Engine"
echo "============================================================"

for f in "$AGENTS/readiness_engine.py" "$CTL/readinessctl" \
 "$MEM/readiness_config.json" "$MEM/readiness_state.json" \
 "$MEM/readiness_report.json" "$MEM/readiness_health.json" \
 "$MEM/autonomous_operations_config.json"; do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/readiness_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_dependency_checks": true,
  "automatic_readiness_scoring": true,
  "automatic_internal_remediation_signals": true,
  "required_controllers": [
    "operationsctl",
    "recoveryctl",
    "learningctl",
    "resourcctl",
    "actionctl",
    "healthctl",
    "missionctl",
    "governancectl",
    "outcomectl",
    "strategyfeedbackctl"
  ],
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false,
  "credential_access": false,
  "private_key_access": false
}
JSON

cat > "$AGENTS/readiness_engine.py" <<'PY'
#!/usr/bin/env python3
import json, sys
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"; C=R/"companyos"
CFG=M/"readiness_config.json"; STATE=M/"readiness_state.json"
REPORT=M/"readiness_report.json"; HEALTH=M/"readiness_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def check():
    cfg=load(CFG,{})
    required=cfg.get("required_controllers",[])
    controllers=[]
    missing=[]
    for name in required:
        p=C/name
        ok=p.exists() and p.stat().st_size>0
        controllers.append({"name":name,"ready":ok})
        if not ok: missing.append(name)

    health_files=list(M.glob("*_health.json"))
    healthy=0; unhealthy=[]; unreadable=[]
    for p in health_files:
        try:
            d=json.loads(p.read_text())
            if d.get("healthy") is False: unhealthy.append(p.name)
            else: healthy+=1
        except Exception:
            unreadable.append(p.name)

    scheduler=M/"autonomous_operations_config.json"
    scheduler_ok=False; enabled_jobs=0
    try:
        d=json.loads(scheduler.read_text())
        jobs=d.get("jobs",[])
        enabled_jobs=sum(1 for x in jobs if x.get("enabled") is True)
        scheduler_ok=enabled_jobs>0
    except Exception: pass

    total_checks=len(required)+1+len(health_files)
    passed=(len(required)-len(missing))+(1 if scheduler_ok else 0)+healthy
    score=round(100*passed/max(1,total_checks),2)

    issues=[]
    if missing: issues.append({"type":"missing_controllers","items":missing})
    if unhealthy: issues.append({"type":"unhealthy_components","items":unhealthy})
    if unreadable: issues.append({"type":"unreadable_health_files","items":unreadable})
    if not scheduler_ok: issues.append({"type":"scheduler_not_ready"})

    report={"generated_at":now(),"readiness_score":score,
            "controllers":controllers,"enabled_scheduler_jobs":enabled_jobs,
            "health_files_checked":len(health_files),"issues":issues,
            "ready":not missing and scheduler_ok and not unhealthy and not unreadable}
    save(REPORT,report)
    old=load(STATE,{})
    save(STATE,{"generated_at":now(),"cycle_count":int(old.get("cycle_count",0))+1,
                "readiness_score":score,"issue_count":len(issues),
                "ready":report["ready"]})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),
                 "system_ready":report["ready"],"readiness_score":score,
                 "issue_count":len(issues)})
    return {"success":True,"status":"readiness_check_complete","report":report}

def status():
    return {"success":True,"status":"readiness_status",
            "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=check() if a=="check" else status() if a=="status" else {
 "success":False,"status":"unknown_action","allowed":["check","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/readiness_engine.py"

cat > "$CTL/readinessctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call(
 [sys.executable,str(r/"agents"/"readiness_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/readinessctl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/readiness_engine.py" "$CTL/readinessctl"

echo "[2/5] Running readiness check..."
python "$CTL/readinessctl" check

echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
j={"id":"dependency-readiness","enabled":True,"interval_seconds":1800,
   "command":["python","companyos/readinessctl","check"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY

echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
python "$CTL/readinessctl" status

echo "[5/5] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"readiness_engine.py",r/"companyos"/"readinessctl",
r/"ceo_memory"/"readiness_config.json",r/"ceo_memory"/"readiness_state.json",
r/"ceo_memory"/"readiness_report.json",r/"ceo_memory"/"readiness_health.json",
r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
try:
    c=json.loads(req[2].read_text())
    for k in ["automatic_customer_contact","automatic_publication","automatic_spending",
              "automatic_destructive_actions","credential_access","private_key_access"]:
        if c.get(k) is not False:errors.append(f"{k} must remain disabled")
    s=json.loads(req[6].read_text())
    j=next((x for x in s.get("jobs",[]) if x.get("id")=="dependency-readiness"),None)
    if not j or j.get("enabled") is not True:errors.append("Readiness scheduler job missing/disabled")
except Exception as e:errors.append(str(e))
print("--------------------------------------------")
print("Phase 18 Step 19 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 18 STEP 19 INSTALLED"
echo " AUTONOMOUS DEPENDENCY & READINESS ENGINE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/readinessctl check"
echo "  python companyos/readinessctl status"
