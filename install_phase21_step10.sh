#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 10 - Adaptive Opportunity Cycle Orchestrator"
echo "============================================================"

cat > "$MEM/opportunity_cycle_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_cycle": true,
  "run_alignment": true,
  "run_reranking": true,
  "run_activation": true,
  "run_translation": true,
  "run_queue_coordination": true,
  "run_handoff": true,
  "run_guarded_execution": true,
  "run_outcome_feedback": true,
  "automatic_external_write": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/adaptive_opportunity_cycle.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"opportunity_cycle_config.json"; STATE=MEM/"opportunity_cycle_state.json"
REPORT=MEM/"opportunity_cycle_report.json"; HEALTH=MEM/"opportunity_cycle_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def call(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=600)
        return {"success":p.returncode==0,"return_code":p.returncode,
                "stdout":p.stdout[-2500:],"stderr":p.stderr[-1200:]}
    except Exception as e:return {"success":False,"error":str(e)}

STEPS=[
("run_alignment","strategic_alignment",["python","companyos/strategicalignctl","align"]),
("run_reranking","learned_reranking",["python","companyos/opportunityrerankctl","rerank"]),
("run_activation","activation",["python","companyos/opportunityactivatectl","activate"]),
("run_translation","translation",["python","companyos/opportunitytranslatectl","translate"]),
("run_queue_coordination","queue_coordination",["python","companyos/opportunityqueuectl","coordinate"]),
("run_handoff","execution_handoff",["python","companyos/actionhandoffctl","handoff"]),
("run_guarded_execution","guarded_execution",["python","companyos/opportunityexecctl","run"]),
("run_outcome_feedback","outcome_feedback",["python","companyos/opportunityoutcomectl","analyze"])
]

def cycle():
    cfg=load(CFG,{})
    results=[]
    for flag,name,cmd in STEPS:
        if cfg.get(flag,True):
            results.append({"step":name,"result":call(cmd)})
    failures=[x["step"] for x in results if not x["result"].get("success")]
    report={"generated_at":now(),"steps":results,"failure_count":len(failures),"failed_steps":failures,
            "automatic_external_write":False,"automatic_customer_contact":False,
            "automatic_publication":False,"automatic_spending":False,"automatic_code_changes":False,
            "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_cycle_at":now(),"failure_count":len(failures),"failed_steps":failures})
    save(HEALTH,{"healthy":len(failures)==0,"last_checked_at":now(),"failure_count":len(failures)})
    return {"success":len(failures)==0,"status":"adaptive_opportunity_cycle_complete","report":report}

def status():
    return {"success":True,"status":"adaptive_opportunity_cycle_status",
            "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=cycle() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/adaptive_opportunity_cycle.py"

cat > "$CTL/opportunitycyclectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"adaptive_opportunity_cycle.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/opportunitycyclectl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/adaptive_opportunity_cycle.py" "$CTL/opportunitycyclectl"
echo "[2/6] Running adaptive opportunity cycle..."
python "$CTL/opportunitycyclectl" run || true
echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"adaptive-opportunity-cycle","enabled":True,"interval_seconds":21600,
"command":["python","companyos/opportunitycyclectl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/opportunitycyclectl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"adaptive_opportunity_cycle.py",r/"companyos"/"opportunitycyclectl",
r/"ceo_memory"/"opportunity_cycle_config.json",r/"ceo_memory"/"opportunity_cycle_state.json",
r/"ceo_memory"/"opportunity_cycle_report.json",r/"ceo_memory"/"opportunity_cycle_health.json",
r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads(req[2].read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
"automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads(req[6].read_text())
if not any(x.get("id")=="adaptive-opportunity-cycle" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------");print("Phase 21 Step 10 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY
echo
echo "============================================================"
echo " PHASE 21 STEP 10 INSTALLED"
echo " ADAPTIVE OPPORTUNITY CYCLE ORCHESTRATOR ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/opportunitycyclectl run"
echo "  python companyos/opportunitycyclectl status"
