#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 20 - Specialist Insight Integration Engine"
echo "============================================================"

cat > "$MEM/specialist_insight_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_integration": true,
  "maximum_insights_per_cycle": 20,
  "require_completed_result": true,
  "minimum_confidence": 0.5,
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

cat > "$AGENTS/specialist_insight_integrator.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"specialist_insight_config.json"
RESULTS=MEM/"specialist_work_results.json"
STATE=MEM/"specialist_insight_state.json"; REPORT=MEM/"specialist_insight_report.json"
HEALTH=MEM/"specialist_insight_health.json"; OUT=MEM/"ceo_specialist_insights.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def num(v,d=0):
    try:return float(v)
    except:return float(d)

def integrate():
    cfg=load(CFG,{})
    rows=load(RESULTS,{}).get("results",[])
    maximum=int(cfg.get("maximum_insights_per_cycle",20))
    require_completed=bool(cfg.get("require_completed_result",True))
    minimum=num(cfg.get("minimum_confidence",.5))
    accepted=[];pending=[];rejected=[]

    for row in rows[:maximum]:
        status=str(row.get("status",""))
        actual=row.get("actual_result")
        if require_completed and (status not in ("completed","validated") or not isinstance(actual,dict)):
            pending.append({"result_id":row.get("result_id"),"reason":"awaiting_completed_specialist_output"})
            continue
        confidence=num(actual.get("confidence",0) if isinstance(actual,dict) else 0)
        if confidence<minimum:
            rejected.append({"result_id":row.get("result_id"),"reason":"confidence_below_threshold",
                             "confidence":confidence})
            continue
        accepted.append({
          "insight_id":f"{row.get('result_id')}-insight",
          "opportunity_id":row.get("opportunity_id"),"title":row.get("title"),
          "specialist_role":row.get("specialist_role"),"specialist":row.get("specialist"),
          "confidence":confidence,
          "summary":actual.get("summary"),"findings":actual.get("findings",[]),
          "recommendations":actual.get("recommendations",[]),"risks":actual.get("risks",[]),
          "next_internal_actions":actual.get("next_internal_actions",[]),
          "decision_status":"available_for_ceo_reasoning",
          "integrated_at":now()
        })

    payload={"generated_at":now(),"insight_count":len(accepted),"insights":accepted,
             "note":"Insights inform internal CEO reasoning only; they do not authorize external actions."}
    save(OUT,payload)
    report={"generated_at":now(),"accepted_count":len(accepted),"pending_count":len(pending),
      "rejected_count":len(rejected),"accepted":accepted,"pending":pending,"rejected":rejected,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_integrated_at":now(),"accepted_count":len(accepted),
      "pending_count":len(pending),"rejected_count":len(rejected)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"accepted_count":len(accepted)})
    return {"success":True,"status":"specialist_insight_integration_complete","report":report}

def status():
    return {"success":True,"status":"specialist_insight_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"insights":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=integrate() if a=="integrate" else status() if a=="status" else {"success":False,"allowed":["integrate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/specialist_insight_integrator.py"

cat > "$CTL/specialistinsightctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"specialist_insight_integrator.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/specialistinsightctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/specialist_insight_integrator.py" "$CTL/specialistinsightctl"
echo "[2/6] Integrating completed specialist insights..."
python "$CTL/specialistinsightctl" integrate
echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"specialist-insight-integration","enabled":True,"interval_seconds":21600,
"command":["python","companyos/specialistinsightctl","integrate"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/specialistinsightctl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"specialist_insight_integrator.py",r/"companyos"/"specialistinsightctl",
r/"ceo_memory"/"specialist_insight_config.json",r/"ceo_memory"/"specialist_insight_state.json",
r/"ceo_memory"/"specialist_insight_report.json",r/"ceo_memory"/"specialist_insight_health.json",
r/"ceo_memory"/"ceo_specialist_insights.json",r/"ceo_memory"/"autonomous_operations_config.json"]
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
if not any(x.get("id")=="specialist-insight-integration" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------");print("Phase 21 Step 20 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 20 INSTALLED"
echo " SPECIALIST INSIGHT INTEGRATION ENGINE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/specialistinsightctl integrate"
echo "  python companyos/specialistinsightctl status"
