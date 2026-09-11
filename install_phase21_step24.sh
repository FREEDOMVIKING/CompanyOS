#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 24 - Governed Internal Execution Queue"
echo "============================================================"

cat > "$MEM/governed_execution_queue_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_queueing": true,
  "maximum_items_per_cycle": 25,
  "allowed_authority": ["internal_non_destructive_only"],
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

cat > "$AGENTS/governed_internal_execution_queue.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"governed_execution_queue_config.json"
PLANS=MEM/"governed_internal_execution_plans.json"
QUEUE=MEM/"governed_internal_work_queue.json"
STATE=MEM/"governed_execution_queue_state.json"
REPORT=MEM/"governed_execution_queue_report.json"
HEALTH=MEM/"governed_execution_queue_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def enqueue():
    cfg=load(CFG,{})
    plans=load(PLANS,{}).get("plans",[])
    old=load(QUEUE,{"work_items":[]}).get("work_items",[])
    existing={x.get("work_id"):x for x in old if x.get("work_id")}
    allowed_auth=set(cfg.get("allowed_authority",[]))
    allowed_types=set(cfg.get("allowed_action_types",[]))
    maximum=int(cfg.get("maximum_items_per_cycle",25))
    added=[];blocked=[]

    for plan in plans:
        if plan.get("execution_authority") not in allowed_auth:
            blocked.append({"plan_id":plan.get("plan_id"),"reason":"authority_not_allowed"});continue
        for step in plan.get("steps",[]):
            if len(added)>=maximum: break
            action_type=step.get("action_type")
            if action_type not in allowed_types:
                blocked.append({"plan_id":plan.get("plan_id"),"step":step.get("step"),"reason":"action_type_not_allowed"});continue
            wid=f"{plan.get('plan_id')}-step-{step.get('step')}"
            if wid in existing: continue
            item={
              "work_id":wid,"plan_id":plan.get("plan_id"),"decision_id":plan.get("decision_id"),
              "opportunity_id":plan.get("opportunity_id"),"title":plan.get("title"),
              "step":step.get("step"),"action_type":action_type,"instruction":step.get("instruction"),
              "execution_authority":"internal_non_destructive_only","status":"queued",
              "attempts":0,"queued_at":now()
            }
            existing[wid]=item;added.append(item)

    all_items=list(existing.values())
    payload={"generated_at":now(),"queued_count":len(all_items),"work_items":all_items}
    save(QUEUE,payload)
    report={"generated_at":now(),"added_count":len(added),"total_queued_count":len(all_items),
      "blocked_count":len(blocked),"added":added,"blocked":blocked,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_enqueued_at":now(),"added_count":len(added),"total_queued_count":len(all_items)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"total_queued_count":len(all_items)})
    return {"success":True,"status":"governed_internal_queue_complete","report":report}

def status():
    return {"success":True,"status":"governed_execution_queue_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"queue":load(QUEUE,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=enqueue() if a=="enqueue" else status() if a=="status" else {"success":False,"allowed":["enqueue","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/governed_internal_execution_queue.py"

cat > "$CTL/governedqueuectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"governed_internal_execution_queue.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/governedqueuectl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/governed_internal_execution_queue.py" "$CTL/governedqueuectl"
echo "[2/6] Queueing governed internal work..."
python "$CTL/governedqueuectl" enqueue
echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"governed-internal-execution-queue","enabled":True,"interval_seconds":21600,
"command":["python","companyos/governedqueuectl","enqueue"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/governedqueuectl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"governed_internal_execution_queue.py",r/"companyos"/"governedqueuectl",
r/"ceo_memory"/"governed_execution_queue_config.json",r/"ceo_memory"/"governed_execution_queue_state.json",
r/"ceo_memory"/"governed_execution_queue_report.json",r/"ceo_memory"/"governed_execution_queue_health.json",
r/"ceo_memory"/"governed_internal_work_queue.json",r/"ceo_memory"/"autonomous_operations_config.json"]
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
if not any(x.get("id")=="governed-internal-execution-queue" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------");print("Phase 21 Step 24 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 24 INSTALLED"
echo " GOVERNED INTERNAL EXECUTION QUEUE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/governedqueuectl enqueue"
echo "  python companyos/governedqueuectl status"
