#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 20 Step 16 - Execution Outcome Feedback Bridge"
echo "============================================================"

cat > "$MEM/execution_feedback_config.json" <<'JSON'
{
  "enabled": true,
  "minimum_samples_before_adjustment": 3,
  "success_adjustment": 2.0,
  "failure_adjustment": -4.0,
  "blocked_adjustment": 0.0,
  "maximum_absolute_adjustment": 15.0,
  "automatic_external_write": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/execution_feedback_bridge.py" <<'PY'
#!/usr/bin/env python3
import json, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
CFG=MEM/"execution_feedback_config.json"
EXEC=MEM/"guarded_executor_report.json"
STATE=MEM/"execution_feedback_state.json"
REPORT=MEM/"execution_feedback_report.json"
HEALTH=MEM/"execution_feedback_health.json"
HISTORY=MEM/"execution_feedback_history.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try: return json.loads(p.read_text())
    except Exception: return d
def save(p,d): p.write_text(json.dumps(d,indent=2),encoding="utf-8")

def analyze():
    cfg=load(CFG,{})
    latest=load(EXEC,{})
    hist=load(HISTORY,{"actions":{}})
    actions=hist.setdefault("actions",{})

    for r in latest.get("results",[]):
        name=r.get("action")
        if not name: continue
        rec=actions.setdefault(name,{"success":0,"failed":0,"blocked":0,"samples":0})
        status=r.get("status","blocked")
        if status not in ("success","failed","blocked"): status="blocked"
        rec[status]+=1
        rec["samples"]+=1

    min_samples=int(cfg.get("minimum_samples_before_adjustment",3))
    max_adj=float(cfg.get("maximum_absolute_adjustment",15))
    adjustments=[]

    for name,rec in actions.items():
        samples=max(1,int(rec.get("samples",0)))
        successes=int(rec.get("success",0))
        failures=int(rec.get("failed",0))
        blocked=int(rec.get("blocked",0))
        raw=(successes*float(cfg.get("success_adjustment",2.0))+
             failures*float(cfg.get("failure_adjustment",-4.0))+
             blocked*float(cfg.get("blocked_adjustment",0.0)))
        adjustment=max(-max_adj,min(max_adj,raw)) if samples>=min_samples else 0.0
        confidence=min(1.0,samples/10.0)
        adjustments.append({
          "action":name,"samples":samples,"success":successes,"failed":failures,
          "blocked":blocked,"feedback_adjustment":round(adjustment,2),
          "confidence":round(confidence,2),
          "eligible_for_adjustment":samples>=min_samples
        })

    adjustments.sort(key=lambda x:(x["feedback_adjustment"],x["confidence"]),reverse=True)
    report={
      "generated_at":now(),
      "adjustments":adjustments,
      "action_count":len(adjustments),
      "automatic_external_write":False,
      "automatic_code_changes":False,
      "automatic_merge":False,
      "automatic_deploy":False,
      "automatic_publication":False,
      "automatic_spending":False,
      "automatic_destructive_actions":False
    }
    save(HISTORY,hist); save(REPORT,report)
    save(STATE,{"last_analyzed_at":now(),"action_count":len(adjustments)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"action_count":len(adjustments)})
    return {"success":True,"status":"execution_feedback_complete","report":report}

def status():
    return {"success":True,"status":"execution_feedback_status",
            "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=analyze() if a=="analyze" else status() if a=="status" else {"success":False,"allowed":["analyze","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/execution_feedback_bridge.py"

cat > "$CTL/executionfeedbackctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"execution_feedback_bridge.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/executionfeedbackctl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/execution_feedback_bridge.py" "$CTL/executionfeedbackctl"

echo "[2/5] Analyzing guarded execution outcomes..."
python "$CTL/executionfeedbackctl" analyze

echo "[3/5] Checking feedback status..."
python "$CTL/executionfeedbackctl" status

echo "[4/5] Verifying safety policy..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"execution_feedback_config.json"
d=json.loads(p.read_text())
keys=["automatic_external_write","automatic_code_changes","automatic_merge",
"automatic_deploy","automatic_publication","automatic_spending","automatic_destructive_actions"]
bad=[k for k in keys if d.get(k) is not False]
if bad: raise SystemExit("Unsafe flags enabled: "+",".join(bad))
print('{"success": true, "safety_policy": "verified"}')
PY

echo "[5/5] Complete."
echo
echo "============================================================"
echo " PHASE 20 STEP 16 INSTALLED"
echo " EXECUTION OUTCOME FEEDBACK BRIDGE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/executionfeedbackctl analyze"
echo "  python companyos/executionfeedbackctl status"
