#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 18 - Controlled Multi-Agent Work Router"
echo "============================================================"

cat > "$MEM/multiagent_router_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_routing": true,
  "maximum_work_items_per_cycle": 10,
  "allowed_work_modes": ["analyze", "research", "plan", "review"],
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

cat > "$AGENTS/controlled_multiagent_router.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"multiagent_router_config.json"
ASSIGN=MEM/"specialist_assignment_plan.json"
STATE=MEM/"multiagent_router_state.json"
REPORT=MEM/"multiagent_router_report.json"
HEALTH=MEM/"multiagent_router_health.json"
QUEUE=MEM/"multiagent_work_queue.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def mode(role):
    return {
      "research":"research","strategy":"plan","product":"plan","engineering":"review",
      "operations":"plan","marketing":"research","finance":"analyze"
    }.get(role,"analyze")

def route():
    cfg=load(CFG,{})
    assignments=load(ASSIGN,{}).get("assignments",[])
    maximum=int(cfg.get("maximum_work_items_per_cycle",10))
    allowed=set(cfg.get("allowed_work_modes",[]))
    queued=[];blocked=[]

    for item in assignments[:maximum]:
        role=item.get("specialist_role","strategy")
        work_mode=mode(role)
        work={
          "work_id":item.get("assignment_id"),
          "opportunity_id":item.get("opportunity_id"),
          "title":item.get("title"),
          "specialist_role":role,
          "specialist":item.get("specialist"),
          "work_mode":work_mode,
          "instruction":item.get("instruction"),
          "attention_units":item.get("attention_units",0)
        }
        if work_mode not in allowed:
            blocked.append({**work,"status":"blocked","reason":"work_mode_not_allowed"})
            continue
        queued.append({**work,"status":"queued_internal","queued_at":now(),
          "execution_boundary":"internal_non_destructive_only"})

    payload={"generated_at":now(),"queued_count":len(queued),"work_items":queued}
    save(QUEUE,payload)
    report={"generated_at":now(),"queued_count":len(queued),"blocked_count":len(blocked),
      "queued":queued,"blocked":blocked,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_routed_at":now(),"queued_count":len(queued),"blocked_count":len(blocked)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"queued_count":len(queued)})
    return {"success":True,"status":"controlled_multiagent_routing_complete","report":report}

def status():
    return {"success":True,"status":"multiagent_router_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"queue":load(QUEUE,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=route() if a=="route" else status() if a=="status" else {"success":False,"allowed":["route","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/controlled_multiagent_router.py"

cat > "$CTL/multiagentroutectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"controlled_multiagent_router.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/multiagentroutectl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/controlled_multiagent_router.py" "$CTL/multiagentroutectl"
echo "[2/6] Routing specialist assignments..."
python "$CTL/multiagentroutectl" route
echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"controlled-multiagent-router","enabled":True,"interval_seconds":21600,
"command":["python","companyos/multiagentroutectl","route"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/multiagentroutectl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"controlled_multiagent_router.py",r/"companyos"/"multiagentroutectl",
r/"ceo_memory"/"multiagent_router_config.json",r/"ceo_memory"/"multiagent_router_state.json",
r/"ceo_memory"/"multiagent_router_report.json",r/"ceo_memory"/"multiagent_router_health.json",
r/"ceo_memory"/"multiagent_work_queue.json",r/"ceo_memory"/"autonomous_operations_config.json"]
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
if not any(x.get("id")=="controlled-multiagent-router" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------");print("Phase 21 Step 18 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 18 INSTALLED"
echo " CONTROLLED MULTI-AGENT WORK ROUTER ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/multiagentroutectl route"
echo "  python companyos/multiagentroutectl status"
