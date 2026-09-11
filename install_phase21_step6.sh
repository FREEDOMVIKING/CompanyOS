#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 6 - Ready Action Execution Handoff"
echo "============================================================"

cat > "$MEM/action_handoff_config.json" <<'JSON'
{
  "enabled": true,
  "max_handoffs_per_cycle": 10,
  "allowed_categories": ["internal_read_only", "internal_reversible", "external_read_only"],
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

cat > "$AGENTS/action_execution_handoff.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"action_handoff_config.json"
SRC=MEM/"opportunity_ready_queue.json"
OUT=MEM/"execution_handoff_queue.json"
STATE=MEM/"action_handoff_state.json"
REPORT=MEM/"action_handoff_report.json"
HEALTH=MEM/"action_handoff_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2),encoding="utf-8"); t.replace(p)

def handoff():
    cfg=load(CFG,{})
    src=load(SRC,{})
    allowed=set(cfg.get("allowed_categories",[]))
    maximum=int(cfg.get("max_handoffs_per_cycle",10))
    accepted=[]; rejected=[]

    for item in src.get("actions",[])[:maximum]:
        cat=item.get("category","internal_read_only")
        if cat not in allowed:
            rejected.append({**item,"handoff_status":"rejected","reason":"category_not_allowed"})
            continue
        accepted.append({
            **item,
            "handoff_status":"approved_for_guarded_execution",
            "handed_off_at":now(),
            "requires_guarded_executor":True
        })

    payload={"generated_at":now(),"handoff_count":len(accepted),"actions":accepted}
    save(OUT,payload)

    report={
      "generated_at":now(),"accepted_count":len(accepted),"rejected_count":len(rejected),
      "accepted":accepted,"rejected":rejected,
      "automatic_external_write":False,"automatic_customer_contact":False,
      "automatic_publication":False,"automatic_spending":False,
      "automatic_code_changes":False,"automatic_merge":False,"automatic_deploy":False,
      "automatic_destructive_actions":False
    }
    save(REPORT,report)
    save(STATE,{"last_handoff_at":now(),"accepted_count":len(accepted),"rejected_count":len(rejected)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"handoff_count":len(accepted)})
    return {"success":True,"status":"action_execution_handoff_complete","report":report}

def status():
    return {"success":True,"status":"action_execution_handoff_status",
            "state":load(STATE,{}),"health":load(HEALTH,{}),
            "report":load(REPORT,{}),"queue":load(OUT,{})}

cmd=sys.argv[1] if len(sys.argv)>1 else "status"
res=handoff() if cmd=="handoff" else status() if cmd=="status" else {"success":False,"allowed":["handoff","status"]}
print(json.dumps(res,indent=2))
raise SystemExit(0 if res.get("success") else 1)
PY

chmod +x "$AGENTS/action_execution_handoff.py"

cat > "$CTL/actionhandoffctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"action_execution_handoff.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/actionhandoffctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/action_execution_handoff.py" "$CTL/actionhandoffctl"

echo "[2/6] Building guarded execution handoff..."
python "$CTL/actionhandoffctl" handoff

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text()); jobs=d.setdefault("jobs",[])
job={"id":"ready-action-execution-handoff","enabled":True,"interval_seconds":1800,
     "command":["python","companyos/actionhandoffctl","handoff"]}
old=next((x for x in jobs if x.get("id")==job["id"]),None)
if old: old.clear(); old.update(job)
else: jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY

echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart

echo "[5/6] Checking status..."
python "$CTL/actionhandoffctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos"; errors=[]
req=[
r/"agents"/"action_execution_handoff.py",
r/"companyos"/"actionhandoffctl",
r/"ceo_memory"/"action_handoff_config.json",
r/"ceo_memory"/"action_handoff_state.json",
r/"ceo_memory"/"action_handoff_report.json",
r/"ceo_memory"/"action_handoff_health.json",
r/"ceo_memory"/"execution_handoff_queue.json",
r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size==0: errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads(req[2].read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication",
          "automatic_spending","automatic_code_changes","automatic_merge","automatic_deploy",
          "automatic_destructive_actions"]:
    if cfg.get(k) is not False: errors.append(f"{k} must remain disabled")
sched=json.loads(req[7].read_text())
if not any(x.get("id")=="ready-action-execution-handoff" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------")
print("Phase 21 Step 6 verification")
print(f"Errors: {len(errors)}"); print("Warnings: 0")
for e in errors: print("ERROR:",e)
if errors: raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 6 INSTALLED"
echo " READY ACTION EXECUTION HANDOFF ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/actionhandoffctl handoff"
echo "  python companyos/actionhandoffctl status"
