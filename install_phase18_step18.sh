#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase18_step18_$(date +%Y%m%d_%H%M%S)"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 18 Step 18 - Adaptive Strategy Feedback Loop"
echo "============================================================"

for f in "$AGENTS/strategy_feedback_loop.py" "$CTL/strategyfeedbackctl" \
 "$MEM/strategy_feedback_config.json" "$MEM/strategy_feedback_state.json" \
 "$MEM/strategy_feedback_report.json" "$MEM/strategy_feedback_health.json" \
 "$MEM/autonomous_operations_config.json"; do
 [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/strategy_feedback_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_strategy_feedback": true,
  "automatic_goal_attention_signals": true,
  "automatic_learning_trigger": true,
  "automatic_goal_refresh": true,
  "low_progress_threshold": 60,
  "high_progress_threshold": 80,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/strategy_feedback_loop.py" <<'PY'
#!/usr/bin/env python3
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"strategy_feedback_config.json"
OUT=M/"outcome_tracker_report.json"
GOALS=M/"goal_strategy_goals.json"
STATE=M/"strategy_feedback_state.json"
REPORT=M/"strategy_feedback_report.json"
HEALTH=M/"strategy_feedback_health.json"
HALT=M/"HALT_AUTONOMY"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run(cmd):
    try:
        p=subprocess.run(cmd,cwd=R,text=True,capture_output=True,timeout=300)
        return {"success":p.returncode==0,"return_code":p.returncode,
                "stdout":p.stdout[-2500:],"stderr":p.stderr[-1200:]}
    except Exception as e:return {"success":False,"error":str(e)}

def adapt():
    cfg=load(CFG,{})
    if not cfg.get("enabled",True):
        return {"success":False,"status":"strategy_feedback_disabled"}
    if HALT.exists():
        return {"success":False,"status":"autonomy_halted"}

    outcomes=load(OUT,{})
    goals=load(GOALS,{}).get("goals",[])
    rows=outcomes.get("goal_outcomes",[])
    low=float(cfg.get("low_progress_threshold",60))
    high=float(cfg.get("high_progress_threshold",80))

    signals=[]
    for row in rows:
        score=float(row.get("progress_score",0))
        if score<low:
            signals.append({"goal_id":row.get("id"),"signal":"increase_attention",
                            "progress_score":score})
        elif score>=high:
            signals.append({"goal_id":row.get("id"),"signal":"maintain_or_expand",
                            "progress_score":score})

    avg=round(sum(float(x.get("progress_score",0)) for x in rows)/max(1,len(rows)),2)
    actions=[]
    if cfg.get("automatic_learning_trigger",True):
        actions.append({"action":"learning-run",
                        "result":run([sys.executable,"companyos/learningctl","learn"])})
    if cfg.get("automatic_goal_refresh",True):
        actions.append({"action":"goal-refresh",
                        "result":run([sys.executable,"companyos/goalctl","generate"])})

    report={"generated_at":now(),"average_goal_progress":avg,
            "signals":signals,"feedback_actions":actions,
            "goal_count":len(goals)}
    save(REPORT,report)
    save(STATE,{"generated_at":now(),"cycle_count":int(load(STATE,{}).get("cycle_count",0))+1,
                "average_goal_progress":avg,"signal_count":len(signals)})
    failures=[a for a in actions if not a["result"].get("success")]
    save(HEALTH,{"healthy":not failures,"last_run_at":now(),
                 "signal_count":len(signals),"failure_count":len(failures)})
    return {"success":not failures,"status":"strategy_feedback_complete","report":report}

def status():
    return {"success":True,"status":"strategy_feedback_status",
            "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=adapt() if a=="adapt" else status() if a=="status" else {
 "success":False,"status":"unknown_action","allowed":["adapt","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/strategy_feedback_loop.py"

cat > "$CTL/strategyfeedbackctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call(
 [sys.executable,str(r/"agents"/"strategy_feedback_loop.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/strategyfeedbackctl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/strategy_feedback_loop.py" "$CTL/strategyfeedbackctl"
echo "[2/5] Running adaptive feedback cycle..."
python "$CTL/strategyfeedbackctl" adapt
echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
j={"id":"strategy-feedback-loop","enabled":True,"interval_seconds":21600,
   "command":["python","companyos/strategyfeedbackctl","adapt"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY
echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
python "$CTL/strategyfeedbackctl" status
echo "[5/5] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"strategy_feedback_loop.py",r/"companyos"/"strategyfeedbackctl",
r/"ceo_memory"/"strategy_feedback_config.json",r/"ceo_memory"/"strategy_feedback_state.json",
r/"ceo_memory"/"strategy_feedback_report.json",r/"ceo_memory"/"strategy_feedback_health.json",
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
    j=next((x for x in s.get("jobs",[]) if x.get("id")=="strategy-feedback-loop"),None)
    if not j or j.get("enabled") is not True:errors.append("Strategy feedback scheduler job missing/disabled")
except Exception as e:errors.append(str(e))
print("--------------------------------------------")
print("Phase 18 Step 18 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 18 STEP 18 INSTALLED"
echo " ADAPTIVE STRATEGY FEEDBACK LOOP ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/strategyfeedbackctl adapt"
echo "  python companyos/strategyfeedbackctl status"
