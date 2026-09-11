#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 5 - Opportunity Action Queue Coordinator"
echo "============================================================"

cat > "$MEM/opportunity_queue_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_queue_coordination": true,
  "maximum_actions_per_cycle": 10,
  "minimum_priority": 40,
  "require_system_ready": true,
  "require_execution_eligibility": true,
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

cat > "$AGENTS/opportunity_queue_coordinator.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"opportunity_queue_config.json"
SOURCE=MEM/"opportunity_action_queue.json"
ELIGIBILITY=MEM/"execution_eligibility_report.json"

STATE=MEM/"opportunity_queue_state.json"
REPORT=MEM/"opportunity_queue_report.json"
HEALTH=MEM/"opportunity_queue_health.json"
READY_QUEUE=MEM/"opportunity_ready_queue.json"

def now(): return datetime.now(timezone.utc).isoformat()

def load(path:Path, default:Any)->Any:
    try:return json.loads(path.read_text(encoding="utf-8"))
    except:return default

def save(path:Path, data:Any)->None:
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,indent=2),encoding="utf-8")
    tmp.replace(path)

def coordinate():
    cfg=load(CFG,{})
    source=load(SOURCE,{})
    eligibility=load(ELIGIBILITY,{})
    system_ready=eligibility.get("system_ready") is True
    matrix=eligibility.get("eligibility",{})

    minimum=float(cfg.get("minimum_priority",40))
    maximum=int(cfg.get("maximum_actions_per_cycle",10))

    ready=[]
    blocked=[]

    for item in source.get("actions",[])[:maximum]:
        try: priority=float(item.get("priority",50))
        except: priority=50.0
        category=item.get("category","internal_read_only")

        if priority < minimum:
            blocked.append({**item,"reason":"below_minimum_priority"})
            continue

        if cfg.get("require_system_ready",True) and not system_ready:
            blocked.append({**item,"reason":"system_not_ready"})
            continue

        if cfg.get("require_execution_eligibility",True) and not bool(matrix.get(category,False)):
            blocked.append({**item,"reason":"category_not_eligible"})
            continue

        ready.append({
            **item,
            "status":"ready",
            "queued_at":now()
        })

    ready.sort(key=lambda x: float(x.get("priority",0)), reverse=True)

    save(READY_QUEUE,{
        "generated_at":now(),
        "system_ready":system_ready,
        "actions":ready
    })

    report={
        "generated_at":now(),
        "system_ready":system_ready,
        "ready_count":len(ready),
        "blocked_count":len(blocked),
        "ready_actions":ready,
        "blocked_actions":blocked,
        "automatic_external_write":False,
        "automatic_customer_contact":False,
        "automatic_publication":False,
        "automatic_spending":False,
        "automatic_code_changes":False,
        "automatic_merge":False,
        "automatic_deploy":False,
        "automatic_destructive_actions":False
    }

    save(REPORT,report)
    save(STATE,{
        "last_coordinated_at":now(),
        "system_ready":system_ready,
        "ready_count":len(ready),
        "blocked_count":len(blocked),
        "top_action":ready[0]["title"] if ready else None
    })
    save(HEALTH,{
        "healthy":True,
        "last_checked_at":now(),
        "ready_count":len(ready),
        "blocked_count":len(blocked)
    })

    return {
        "success":True,
        "status":"opportunity_queue_coordination_complete",
        "report":report
    }

def status():
    return {
        "success":True,
        "status":"opportunity_queue_status",
        "state":load(STATE,{}),
        "health":load(HEALTH,{}),
        "report":load(REPORT,{}),
        "queue":load(READY_QUEUE,{})
    }

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=coordinate() if a=="coordinate" else status() if a=="status" else {"success":False,"allowed":["coordinate","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/opportunity_queue_coordinator.py"

cat > "$CTL/opportunityqueuectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"opportunity_queue_coordinator.py"),*sys.argv[1:]],cwd=r))
PY

chmod +x "$CTL/opportunityqueuectl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/opportunity_queue_coordinator.py" "$CTL/opportunityqueuectl"

echo "[2/6] Coordinating opportunity action queue..."
python "$CTL/opportunityqueuectl" coordinate

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text())
jobs=d.setdefault("jobs",[])
job={
    "id":"opportunity-action-queue",
    "enabled":True,
    "interval_seconds":1800,
    "command":["python","companyos/opportunityqueuectl","coordinate"]
}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY

echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart

echo "[5/6] Checking queue status..."
python "$CTL/opportunityqueuectl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path

root=Path.home()/"companyos"
errors=[]

required=[
    root/"agents"/"opportunity_queue_coordinator.py",
    root/"companyos"/"opportunityqueuectl",
    root/"ceo_memory"/"opportunity_queue_config.json",
    root/"ceo_memory"/"opportunity_queue_state.json",
    root/"ceo_memory"/"opportunity_queue_report.json",
    root/"ceo_memory"/"opportunity_queue_health.json",
    root/"ceo_memory"/"opportunity_ready_queue.json",
    root/"ceo_memory"/"autonomous_operations_config.json"
]

for p in required:
    if not p.exists() or p.stat().st_size<=0:
        errors.append(f"Missing/empty: {p}")

for p in required[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))

cfg=json.loads(required[2].read_text())
for k in [
    "automatic_external_write",
    "automatic_customer_contact",
    "automatic_publication",
    "automatic_spending",
    "automatic_code_changes",
    "automatic_merge",
    "automatic_deploy",
    "automatic_destructive_actions"
]:
    if cfg.get(k) is not False:
        errors.append(f"{k} must remain disabled")

sched=json.loads(required[7].read_text())
job=next((x for x in sched.get("jobs",[]) if x.get("id")=="opportunity-action-queue"),None)
if not job or job.get("enabled") is not True:
    errors.append("Opportunity action queue scheduler job missing/disabled")

print("--------------------------------------------")
print("Phase 21 Step 5 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 5 INSTALLED"
echo " OPPORTUNITY ACTION QUEUE COORDINATOR ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/opportunityqueuectl coordinate"
echo "  python companyos/opportunityqueuectl status"
