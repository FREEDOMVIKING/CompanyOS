#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 14 - Opportunity Lifecycle & Exit Engine"
echo "============================================================"

cat > "$MEM/opportunity_lifecycle_config.json" <<'JSON'
{
  "enabled": true,
  "stale_after_hours": 168,
  "minimum_keep_score": 50,
  "maximum_failed_cycles": 3,
  "automatic_internal_retirement": true,
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

cat > "$AGENTS/opportunity_lifecycle_manager.py" <<'PY'
#!/usr/bin/env python3
import json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"opportunity_lifecycle_config.json"
PORT=MEM/"rebalanced_opportunity_portfolio.json"
STATE=MEM/"opportunity_lifecycle_state.json"
REPORT=MEM/"opportunity_lifecycle_report.json"
HEALTH=MEM/"opportunity_lifecycle_health.json"
ARCHIVE=MEM/"retired_opportunities.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2),encoding="utf-8")
    t.replace(p)
def score(x):
    try:return float(x.get("final_opportunity_score",0) or 0)
    except:return 0.0

def evaluate():
    cfg=load(CFG,{})
    rows=load(PORT,{}).get("opportunities",[])
    minimum=float(cfg.get("minimum_keep_score",50))
    max_failed=int(cfg.get("maximum_failed_cycles",3))
    archive=load(ARCHIVE,{"retired":[]})
    retired=archive.setdefault("retired",[])
    active=[]; newly_retired=[]

    for row in rows:
        failures=int(row.get("failed_cycles",0) or 0)
        reason=None
        if score(row)<minimum:
            reason="score_below_keep_threshold"
        elif failures>=max_failed:
            reason="repeated_failed_cycles"

        if reason:
            item={
              "id":row.get("id"),"title":row.get("title"),
              "category":row.get("category"),
              "final_opportunity_score":row.get("final_opportunity_score"),
              "retired_at":now(),"reason":reason,
              "status":"retired_internal"
            }
            retired.append(item);newly_retired.append(item)
        else:
            x=dict(row);x["lifecycle_status"]="active";active.append(x)

    archive["updated_at"]=now()
    save(ARCHIVE,archive)

    report={
      "generated_at":now(),"evaluated_count":len(rows),
      "active_count":len(active),"retired_count":len(newly_retired),
      "active":active,"newly_retired":newly_retired,
      "automatic_external_write":False,"automatic_customer_contact":False,
      "automatic_publication":False,"automatic_spending":False,
      "automatic_code_changes":False,"automatic_merge":False,
      "automatic_deploy":False,"automatic_destructive_actions":False
    }
    save(REPORT,report)
    save(STATE,{"last_evaluated_at":now(),"active_count":len(active),
                "retired_count":len(newly_retired)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),
                 "evaluated_count":len(rows)})
    return {"success":True,"status":"opportunity_lifecycle_evaluation_complete","report":report}

def status():
    return {"success":True,"status":"opportunity_lifecycle_status",
            "state":load(STATE,{}),"health":load(HEALTH,{}),
            "report":load(REPORT,{}),"archive":load(ARCHIVE,{"retired":[]})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=evaluate() if a=="evaluate" else status() if a=="status" else {
  "success":False,"allowed":["evaluate","status"]
}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/opportunity_lifecycle_manager.py"

cat > "$CTL/opportunitylifecyclectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call(
 [sys.executable,str(r/"agents"/"opportunity_lifecycle_manager.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/opportunitylifecyclectl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/opportunity_lifecycle_manager.py" "$CTL/opportunitylifecyclectl"

echo "[2/6] Evaluating opportunity lifecycle..."
python "$CTL/opportunitylifecyclectl" evaluate

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"opportunity-lifecycle","enabled":True,"interval_seconds":21600,
"command":["python","companyos/opportunitylifecyclectl","evaluate"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY

echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart

echo "[5/6] Checking status..."
python "$CTL/opportunitylifecyclectl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"opportunity_lifecycle_manager.py",
r/"companyos"/"opportunitylifecyclectl",
r/"ceo_memory"/"opportunity_lifecycle_config.json",
r/"ceo_memory"/"opportunity_lifecycle_state.json",
r/"ceo_memory"/"opportunity_lifecycle_report.json",
r/"ceo_memory"/"opportunity_lifecycle_health.json",
r/"ceo_memory"/"retired_opportunities.json",
r/"ceo_memory"/"autonomous_operations_config.json"]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads(req[2].read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication",
"automatic_spending","automatic_code_changes","automatic_merge","automatic_deploy",
"automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads(req[7].read_text())
if not any(x.get("id")=="opportunity-lifecycle" and x.get("enabled")
           for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------")
print("Phase 21 Step 14 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 14 INSTALLED"
echo " OPPORTUNITY LIFECYCLE & EXIT ENGINE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/opportunitylifecyclectl evaluate"
echo "  python companyos/opportunitylifecyclectl status"
