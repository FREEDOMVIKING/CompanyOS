#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/companyos"; AGENTS="$ROOT/agents"; CTL="$ROOT/companyos"; MEM="$ROOT/ceo_memory"
cd "$ROOT"; mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 26 - Real Specialist Runtime Adapter"
echo "============================================================"

cat > "$MEM/specialist_runtime_config.json" <<'JSON'
{
  "enabled": true,
  "provider": "openai_compatible",
  "model": "gpt-4.1-mini",
  "base_url": "https://api.openai.com/v1",
  "api_key_env": "OPENAI_API_KEY",
  "timeout_seconds": 120,
  "maximum_items_per_cycle": 5,
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

cat > "$AGENTS/specialist_runtime_adapter.py" <<'PY'
#!/usr/bin/env python3
import json,os,sys,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"specialist_runtime_config.json"
WORK=MEM/"governed_internal_work_results.json"
OUT=MEM/"specialist_runtime_results.json"
STATE=MEM/"specialist_runtime_state.json"
REPORT=MEM/"specialist_runtime_report.json"
HEALTH=MEM/"specialist_runtime_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def call_model(cfg,item):
    key=os.getenv(cfg.get("api_key_env","OPENAI_API_KEY"),"").strip()
    if not key:return None,"missing_api_key"
    base=cfg.get("base_url","https://api.openai.com/v1").rstrip("/")
    url=base+"/chat/completions"
    system=("You are a specialist worker inside CompanyOS. Perform internal, non-destructive reasoning only. "
            "Do not claim to have contacted people, spent money, deployed, published, modified external systems, "
            "or performed actions you cannot verify. Return ONLY valid JSON with keys: summary, findings, "
            "recommendations, risks, next_internal_actions, confidence. confidence must be 0 to 1.")
    prompt=json.dumps({
      "action_type":item.get("action_type"),
      "instruction":item.get("instruction"),
      "opportunity_id":item.get("opportunity_id"),
      "execution_boundary":"internal_non_destructive_only"
    })
    body=json.dumps({"model":cfg.get("model"),"temperature":0.2,
      "messages":[{"role":"system","content":system},{"role":"user","content":prompt}],
      "response_format":{"type":"json_object"}}).encode()
    req=urllib.request.Request(url,data=body,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=int(cfg.get("timeout_seconds",120))) as r:
            data=json.loads(r.read().decode())
        text=data["choices"][0]["message"]["content"]
        return json.loads(text),None
    except Exception as e:return None,str(e)

def run():
    cfg=load(CFG,{})
    rows=load(WORK,{}).get("results",[])
    previous=load(OUT,{"results":[]}).get("results",[])
    done={x.get("work_id") for x in previous if x.get("status")=="completed"}
    maximum=int(cfg.get("maximum_items_per_cycle",5));completed=[];pending=[]

    for item in rows:
        if len(completed)>=maximum:break
        if item.get("status")!="prepared_for_specialist_runtime" or item.get("work_id") in done:continue
        actual,error=call_model(cfg,item)
        if error:
            pending.append({"work_id":item.get("work_id"),"status":"pending","reason":error})
            continue
        result={
          "work_id":item.get("work_id"),"plan_id":item.get("plan_id"),
          "decision_id":item.get("decision_id"),"opportunity_id":item.get("opportunity_id"),
          "action_type":item.get("action_type"),"status":"completed",
          "actual_result":actual,"completed_at":now(),
          "execution_boundary":"internal_non_destructive_only"
        }
        previous.append(result);completed.append(result)

    save(OUT,{"generated_at":now(),"result_count":len(previous),"results":previous})
    report={"generated_at":now(),"completed_count":len(completed),"pending_count":len(pending),
      "completed":completed,"pending":pending,
      "automatic_external_write":False,"automatic_customer_contact":False,"automatic_publication":False,
      "automatic_spending":False,"automatic_fund_transfer":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,"automatic_destructive_actions":False}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"completed_count":len(completed),"pending_count":len(pending)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"provider":cfg.get("provider"),
      "api_key_available":bool(os.getenv(cfg.get("api_key_env","OPENAI_API_KEY"),"").strip())})
    return {"success":True,"status":"specialist_runtime_cycle_complete","report":report}

def status():
    cfg=load(CFG,{})
    return {"success":True,"status":"specialist_runtime_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(REPORT,{}),"config":{
        "provider":cfg.get("provider"),"model":cfg.get("model"),"base_url":cfg.get("base_url"),
        "api_key_env":cfg.get("api_key_env")}}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/specialist_runtime_adapter.py"

cat > "$CTL/specialistruntimectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"specialist_runtime_adapter.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/specialistruntimectl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/specialist_runtime_adapter.py" "$CTL/specialistruntimectl"
echo "[2/6] Running runtime adapter (safe if API key is not configured yet)..."
python "$CTL/specialistruntimectl" run
echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"specialist-runtime-adapter","enabled":True,"interval_seconds":3600,
"command":["python","companyos/specialistruntimectl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
echo "[5/6] Checking status..."
python "$CTL/specialistruntimectl" status
echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[];warnings=[]
req=[r/"agents"/"specialist_runtime_adapter.py",r/"companyos"/"specialistruntimectl",
r/"ceo_memory"/"specialist_runtime_config.json",r/"ceo_memory"/"specialist_runtime_state.json",
r/"ceo_memory"/"specialist_runtime_report.json",r/"ceo_memory"/"specialist_runtime_health.json",
r/"ceo_memory"/"specialist_runtime_results.json",r/"ceo_memory"/"autonomous_operations_config.json"]
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
if not any(x.get("id")=="specialist-runtime-adapter" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Scheduler job missing/disabled")
import os
if not os.getenv(cfg.get("api_key_env","OPENAI_API_KEY"),"").strip():
    warnings.append("OPENAI_API_KEY not configured; runtime installed but model execution is pending.")
print("--------------------------------------------");print("Phase 21 Step 26 verification")
print(f"Errors: {len(errors)}");print(f"Warnings: {len(warnings)}")
for e in errors:print("ERROR:",e)
for w in warnings:print("WARNING:",w)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 26 INSTALLED"
echo " REAL SPECIALIST RUNTIME ADAPTER ACTIVE"
echo "============================================================"
echo "Commands:"
echo "  python companyos/specialistruntimectl run"
echo "  python companyos/specialistruntimectl status"
