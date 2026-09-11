#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase18_step17_$(date +%Y%m%d_%H%M%S)"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 18 Step 17 - Autonomous KPI & Outcome Tracker"
echo "============================================================"

for f in "$AGENTS/outcome_tracker.py" "$CTL/outcomectl" \
 "$MEM/outcome_tracker_config.json" "$MEM/outcome_tracker_state.json" \
 "$MEM/outcome_tracker_report.json" "$MEM/outcome_tracker_health.json" \
 "$MEM/autonomous_operations_config.json"; do
 [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/outcome_tracker_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_measurement": true,
  "automatic_goal_progress_scoring": true,
  "automatic_internal_feedback": true,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/outcome_tracker.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"outcome_tracker_config.json"; STATE=M/"outcome_tracker_state.json"
REPORT=M/"outcome_tracker_report.json"; HEALTH=M/"outcome_tracker_health.json"
GOALS=M/"goal_strategy_goals.json"; PERF=M/"performance_analytics_report.json"
OPS=M/"autonomous_operations_state.json"; ACTION=M/"internal_action_state.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def measure():
    goals=load(GOALS,{}).get("goals",[])
    perf=load(PERF,{}).get("report",{})
    ops=load(OPS,{})
    actions=load(ACTION,{})
    health=float(perf.get("health_score") or 0)
    jobs=ops.get("jobs",{})
    successes=sum(1 for x in jobs.values() if x.get("last_success") is True)
    failures=sum(1 for x in jobs.values() if x.get("last_success") is False)
    action_failures=int(actions.get("failures",0))
    reliability=round(100*successes/max(1,successes+failures),2)
    goal_rows=[]
    for g in goals:
        base=float(g.get("score",50))
        progress=round(max(0,min(100,base*.45+health*.30+reliability*.25)),2)
        goal_rows.append({"id":g.get("id"),"title":g.get("title"),
                          "rank":g.get("rank"),"progress_score":progress,
                          "status":"on_track" if progress>=70 else "needs_attention"})
    report={"generated_at":now(),"kpis":{
        "operating_health_score":health,"scheduler_reliability_percent":reliability,
        "successful_jobs":successes,"failed_jobs":failures,
        "internal_action_failures":action_failures,"active_goals":len(goals)},
        "goal_outcomes":goal_rows,
        "needs_attention":[x for x in goal_rows if x["status"]=="needs_attention"]}
    save(REPORT,report)
    save(STATE,{"generated_at":now(),"measurement_count":len(goal_rows),
                "average_goal_progress":round(sum(x["progress_score"] for x in goal_rows)/max(1,len(goal_rows)),2)})
    save(HEALTH,{"healthy":True,"last_measured_at":now(),"goal_count":len(goal_rows)})
    return {"success":True,"status":"outcome_measurement_complete","report":report}

def status(): return {"success":True,"status":"outcome_tracker_status",
                      "state":load(STATE,{}),"health":load(HEALTH,{}),
                      "report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=measure() if a=="measure" else status() if a=="status" else {
 "success":False,"status":"unknown_action","allowed":["measure","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/outcome_tracker.py"

cat > "$CTL/outcomectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"outcome_tracker.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/outcomectl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/outcome_tracker.py" "$CTL/outcomectl"
echo "[2/5] Measuring outcomes..."
python "$CTL/outcomectl" measure
echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
j={"id":"outcome-tracker","enabled":True,"interval_seconds":3600,
   "command":["python","companyos/outcomectl","measure"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY
echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
python "$CTL/outcomectl" status
echo "[5/5] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos"; errors=[]
req=[r/"agents"/"outcome_tracker.py",r/"companyos"/"outcomectl",
r/"ceo_memory"/"outcome_tracker_config.json",r/"ceo_memory"/"outcome_tracker_state.json",
r/"ceo_memory"/"outcome_tracker_report.json",r/"ceo_memory"/"outcome_tracker_health.json",
r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
try:
    c=json.loads(req[2].read_text())
    for k in ["automatic_customer_contact","automatic_publication","automatic_spending","automatic_destructive_actions"]:
        if c.get(k) is not False:errors.append(f"{k} must remain disabled")
    s=json.loads(req[6].read_text())
    j=next((x for x in s.get("jobs",[]) if x.get("id")=="outcome-tracker"),None)
    if not j or j.get("enabled") is not True:errors.append("Outcome tracker scheduler job missing/disabled")
except Exception as e:errors.append(str(e))
print("--------------------------------------------")
print("Phase 18 Step 17 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 18 STEP 17 INSTALLED"
echo " AUTONOMOUS KPI & OUTCOME TRACKER ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/outcomectl measure"
echo "  python companyos/outcomectl status"
