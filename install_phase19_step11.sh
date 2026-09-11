#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 19 Step 11 - Autonomous Outcome Feedback Loop"
echo "============================================================"

cat > "$MEM/action_feedback_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_feedback_analysis": true,
  "automatic_priority_adjustment_recommendations": true,
  "automatic_internal_learning_trigger": true,
  "failure_rate_learning_threshold": 0.25,
  "automatic_external_write": false,
  "automatic_code_changes": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/action_feedback_loop.py" <<'PY'
#!/usr/bin/env python3
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"action_feedback_config.json"
QUEUE=MEM/"action_queue_report.json"
OUT=MEM/"action_feedback_report.json"
STATE=MEM/"action_feedback_state.json"
HEALTH=MEM/"action_feedback_health.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

def now(): return datetime.now(timezone.utc).isoformat()

def learn():
    cfg=load(CFG,{})
    q=load(QUEUE,{})
    results=q.get("results",[])
    total=len(results)
    failed=sum(1 for x in results if not x.get("success"))
    rate=(failed/total) if total else 0.0

    rec=[]
    if not total:
        rec.append("No completed action-queue results are available yet.")
    elif rate >= float(cfg.get("failure_rate_learning_threshold",0.25)):
        rec.append("Increase review of failing internal actions before expanding automation.")
    else:
        rec.append("Current internal action execution is within the configured feedback threshold.")

    triggered=False
    learning_result=None
    if total and rate >= float(cfg.get("failure_rate_learning_threshold",0.25)) and cfg.get("automatic_internal_learning_trigger"):
        try:
            p=subprocess.run(
                ["python","companyos/learningctl","learn"],
                cwd=ROOT,text=True,capture_output=True,timeout=300
            )
            triggered=True
            learning_result={"return_code":p.returncode,"success":p.returncode==0,
                             "stdout":p.stdout[-2000:],"stderr":p.stderr[-1000:]}
        except Exception as e:
            triggered=True
            learning_result={"success":False,"error":str(e)}

    report={
      "generated_at":now(),
      "actions_evaluated":total,
      "failed_actions":failed,
      "failure_rate":round(rate,4),
      "learning_triggered":triggered,
      "learning_result":learning_result,
      "recommendations":rec,
      "automatic_external_write":False,
      "automatic_code_changes":False,
      "automatic_publication":False,
      "automatic_spending":False,
      "automatic_destructive_actions":False
    }
    save(OUT,report)
    save(STATE,{"generated_at":now(),"actions_evaluated":total,
                "failed_actions":failed,"failure_rate":round(rate,4)})
    save(HEALTH,{"healthy":True,"last_feedback_at":now(),
                 "learning_triggered":triggered})
    return {"success":True,"status":"action_feedback_complete","report":report}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="learn": r=learn()
elif a=="status":
    r={"success":True,"status":"action_feedback_status",
       "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(OUT,{})}
else:r={"success":False,"status":"unknown_action","allowed":["learn","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/action_feedback_loop.py"

cat > "$CTL/actionfeedbackctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call(
    [sys.executable,str(r/"agents"/"action_feedback_loop.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/actionfeedbackctl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/action_feedback_loop.py" "$CTL/actionfeedbackctl"

echo "[2/5] Running feedback analysis..."
python "$CTL/actionfeedbackctl" learn

echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text()); jobs=d.setdefault("jobs",[])
j={"id":"action-feedback-loop","enabled":True,"interval_seconds":21600,
   "command":["python","companyos/actionfeedbackctl","learn"]}
e=next((x for x in jobs if x.get("id")==j["id"]),None)
if e:e.clear();e.update(j)
else:jobs.append(j)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":j["id"]},indent=2))
PY

echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart

echo "[5/5] Verifying..."
python "$CTL/actionfeedbackctl" status

echo
echo "============================================================"
echo " PHASE 19 STEP 11 INSTALLED"
echo " AUTONOMOUS OUTCOME FEEDBACK LOOP ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/actionfeedbackctl learn"
echo "  python companyos/actionfeedbackctl status"
echo
echo "Autonomous schedule:"
echo "  Outcome feedback analysis runs every 6 hours"
