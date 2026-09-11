#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 19 - Specialist Work Result Collector"
echo "============================================================"

cat > "$MEM/specialist_result_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_result_collection": true,
  "maximum_results_per_cycle": 10,
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

cat > "$AGENTS/specialist_work_result_collector.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"specialist_result_config.json"; QUEUE=MEM/"multiagent_work_queue.json"
STATE=MEM/"specialist_result_state.json"; REPORT=MEM/"specialist_result_report.json"
HEALTH=MEM/"specialist_result_health.json"; OUT=MEM/"specialist_work_results.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def collect():
    cfg=load(CFG,{})
    items=load(QUEUE,{}).get("work_items",[])
    maximum=int(cfg.get("maximum_results_per_cycle",10))
    allowed=set(cfg.get("allowed_work_modes",[]))
    results=[];blocked=[]

    for item in items[:maximum]:
        mode=item.get("work_mode","analyze")
        if mode not in allowed:
            blocked.append({"work_id":item.get("work_id"),"reason":"work_mode_not_allowed"})
            continue
        results.append({
          "result_id":f"{item.get('work_id')}-result",
          "work_id":item.get("work_id"),"opportunity_id":item.get("opportunity_id"),
          "title":item.get("title"),"specialist_role":item.get("specialist_role"),
          "specialist":item.get("specialist"),"work_mode":mode,
          "status":"ready_for_internal_specialist_processing",
          "requested_output":{
            "summary":True,"findings":True,"recommendations":True,
            "risks":True,"next_internal_actions":True
          },
          "execution_boundary":"internal_non_destructive_only",
          "created_at":now()
        })

    payload={"generated_at":now(),"result_request_count":len(results),"results":results}
    save(OUT,payload)
    report={"generated_at":now(),"prepared_count":len(results),"blocked_count":len(blocked),
      "prepared":results,"blocked":blocked,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_collected_at":now(),"prepared_count":len(results),"blocked_count":len(blocked)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"prepared_count":len(results)})
    return {"success":True,"status":"specialist_work_result_collection_complete","report":report}

def status():
    return {"success":True,"status":"specialist_result_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"results":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=collect() if a=="collect" else status() if a=="status" else {"success":False,"allowed":["collect","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/specialist_work_result_collector.py"

cat > "$CTL/specialistresultctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"specialist_work_result_collector.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/specialistresultctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/specialist_work_result_collector.py" "$CTL/specialistresultctl"
echo "[2/6] Preparing specialist result requests..."
python "$CTL/specialistresultctl" collect
echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"specialist-work-result-collector","enabled":True,"interval_seconds":21600,
"command":["python","companyos/specialistresultctl","collect"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/specialistresultctl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[r/"agents"/"specialist_work_result_collector.py",r/"companyos"/"specialistresultctl",
r/"ceo_memory"/"specialist_result_config.json",r/"ceo_memory"/"specialist_result_state.json",
r/"ceo_memory"/"specialist_result_report.json",r/"ceo_memory"/"specialist_result_health.json",
r/"ceo_memory"/"specialist_work_results.json",r/"ceo_memory"/"autonomous_operations_config.json"]
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
if not any(x.get("id")=="specialist-work-result-collector" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
print("--------------------------------------------");print("Phase 21 Step 19 verification")
print(f"Errors: {len(errors)}");print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 19 INSTALLED"
echo " SPECIALIST WORK RESULT COLLECTOR ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo "Commands:"
echo "  python companyos/specialistresultctl collect"
echo "  python companyos/specialistresultctl status"
