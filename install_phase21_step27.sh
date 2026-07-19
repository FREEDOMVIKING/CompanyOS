#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 27 - Live Specialist Task Bridge"
echo "============================================================"

cat > "$MEM/specialist_bridge_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_bridge": true,
  "maximum_tasks_per_cycle": 10,
  "allowed_action_types": ["analyze", "research", "plan", "review", "prioritize", "coordinate"],
  "automatic_external_write": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_fund_transfer": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/live_specialist_task_bridge.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"specialist_bridge_config.json"
SOURCE=MEM/"governed_internal_work_results.json"
TARGET=MEM/"specialist_runtime_input_queue.json"
STATE=MEM/"specialist_bridge_state.json"
REPORT=MEM/"specialist_bridge_report.json"
HEALTH=MEM/"specialist_bridge_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def bridge():
    cfg=load(CFG,{})
    rows=load(SOURCE,{}).get("results",[])
    existing=load(TARGET,{"tasks":[]}).get("tasks",[])
    seen={x.get("work_id") for x in existing if x.get("work_id")}
    allowed=set(cfg.get("allowed_action_types",[]))
    maximum=int(cfg.get("maximum_tasks_per_cycle",10))
    added=[];blocked=[]

    for row in rows:
        if len(added)>=maximum: break
        if row.get("status")!="prepared_for_specialist_runtime": continue
        wid=row.get("work_id")
        if not wid or wid in seen: continue
        action=row.get("action_type")
        if action not in allowed:
            blocked.append({"work_id":wid,"reason":"action_type_not_allowed"})
            continue
        task={
          "work_id":wid,
          "plan_id":row.get("plan_id"),
          "decision_id":row.get("decision_id"),
          "opportunity_id":row.get("opportunity_id"),
          "action_type":action,
          "instruction":row.get("instruction"),
          "execution_boundary":"internal_non_destructive_only",
          "status":"queued_for_live_specialist",
          "queued_at":now()
        }
        existing.append(task);added.append(task);seen.add(wid)

    payload={"generated_at":now(),"task_count":len(existing),"tasks":existing}
    save(TARGET,payload)

    report={
      "generated_at":now(),
      "added_count":len(added),
      "blocked_count":len(blocked),
      "total_task_count":len(existing),
      "added":added,
      "blocked":blocked,
      "automatic_external_write":False,
      "automatic_customer_contact":False,
      "automatic_publication":False,
      "automatic_spending":False,
      "automatic_fund_transfer":False,
      "automatic_code_changes":False,
      "automatic_merge":False,
      "automatic_deploy":False,
      "automatic_destructive_actions":False
    }
    save(REPORT,report)
    save(STATE,{"last_bridged_at":now(),"added_count":len(added),"total_task_count":len(existing)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"task_count":len(existing)})
    return {"success":True,"status":"live_specialist_bridge_complete","report":report}

def status():
    return {"success":True,"status":"live_specialist_bridge_status",
      "state":load(STATE,{}),"health":load(HEALTH,{}),
      "report":load(REPORT,{}),"queue":load(TARGET,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=bridge() if a=="bridge" else status() if a=="status" else {"success":False,"allowed":["bridge","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/live_specialist_task_bridge.py"

cat > "$CTL/specialistbridgectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"live_specialist_task_bridge.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/specialistbridgectl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/live_specialist_task_bridge.py" "$CTL/specialistbridgectl"

echo "[2/6] Bridging governed work to live specialist queue..."
python "$CTL/specialistbridgectl" bridge

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"live-specialist-task-bridge","enabled":True,"interval_seconds":1800,
"command":["python","companyos/specialistbridgectl","bridge"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY

echo "[4/6] Restarting operations scheduler..."
python "$CTL/operationsctl" restart

echo "[5/6] Checking bridge status..."
python "$CTL/specialistbridgectl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"live_specialist_task_bridge.py",
r/"companyos"/"specialistbridgectl",
r/"ceo_memory"/"specialist_bridge_config.json",
r/"ceo_memory"/"specialist_bridge_state.json",
r/"ceo_memory"/"specialist_bridge_report.json",
r/"ceo_memory"/"specialist_bridge_health.json",
r/"ceo_memory"/"specialist_runtime_input_queue.json",
r/"ceo_memory"/"autonomous_operations_config.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads(req[2].read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
"automatic_fund_transfer","automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads(req[7].read_text())
if not any(x.get("id")=="live-specialist-task-bridge" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------")
print("Phase 21 Step 27 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 27 INSTALLED"
echo " LIVE SPECIALIST TASK BRIDGE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/specialistbridgectl bridge"
echo "  python companyos/specialistbridgectl status"
