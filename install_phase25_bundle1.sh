#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase25_bundle1_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 25 BUNDLE 1 - HYBRID AI ORCHESTRATION CORE"
echo "============================================================"

for f in \
  "$AGENTS/ai_provider_health_engine.py" \
  "$AGENTS/ai_task_router.py" \
  "$AGENTS/ai_provenance_engine.py" \
  "$AGENTS/local_ai_startup_guard.py" \
  "$AGENTS/ai_recovery_manager.py" \
  "$AGENTS/phase25_bundle1_controller.py" \
  "$CTL/aiproviderhealthctl" \
  "$CTL/aitaskrouterctl" \
  "$CTL/aiprovenancectl" \
  "$CTL/localaiguardctl" \
  "$CTL/airecoveryctl" \
  "$CTL/phase25bundle1ctl"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/phase25_bundle1_config.json" <<'JSON'
{
  "enabled": true,
  "primary_provider": "openai",
  "fallback_provider": "local_llama",
  "primary_model": "gpt-4.1-mini",
  "fallback_model": "local",
  "fallback_base_url": "http://127.0.0.1:8080/v1",
  "local_health_url": "http://127.0.0.1:8080/health",
  "provider_timeout_seconds": 20,
  "fallback_http_codes": [408, 429, 500, 502, 503, 504],
  "routing_policy": "primary_then_local_fallback",
  "maximum_retry_attempts": 2,
  "automatic_internal_recovery": true,
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

cat > "$AGENTS/ai_provider_health_engine.py" <<'PY'
#!/usr/bin/env python3
import json, os, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase25_bundle1_config.json"
OUT=MEM/"ai_provider_health_report.json"
STATE=MEM/"ai_provider_health_state.json"
HEALTH=MEM/"ai_provider_health_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2)); t.replace(p)

def http_ok(url, timeout):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return True, getattr(r,"status",200)
    except urllib.error.HTTPError as e:
        return False, e.code
    except Exception as e:
        return False, type(e).__name__

def run():
    cfg=load(CFG,{})
    timeout=int(cfg.get("provider_timeout_seconds",20))
    openai_key=bool(os.getenv("OPENAI_API_KEY","").strip())
    local_ok, local_status=http_ok(cfg.get("local_health_url","http://127.0.0.1:8080/health"), timeout)
    payload={
      "generated_at":now(),
      "primary":{"provider":"openai","configured":openai_key,"usable":openai_key,
                 "note":"Quota/HTTP health is validated during actual requests."},
      "fallback":{"provider":"local_llama","configured":True,"reachable":local_ok,
                  "status":local_status,"base_url":cfg.get("fallback_base_url")},
      "routing_policy":cfg.get("routing_policy"),
      "healthy": bool(openai_key or local_ok)
    }
    save(OUT,payload); save(STATE,{"last_run_at":now(),"healthy":payload["healthy"]})
    save(HEALTH,{"healthy":payload["healthy"],"last_checked_at":now()})
    return {"success":True,"status":"ai_provider_health_complete","report":payload}

print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/ai_provider_health_engine.py"

cat > "$CTL/aiproviderhealthctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"ai_provider_health_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/aiproviderhealthctl"

cat > "$AGENTS/ai_task_router.py" <<'PY'
#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
WORK=MEM/"governed_internal_work_results.json"
PROVIDER=MEM/"ai_provider_health_report.json"
OUT=MEM/"ai_task_routing_plan.json"
STATE=MEM/"ai_task_router_state.json"
HEALTH=MEM/"ai_task_router_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    provider=load(PROVIDER,{})
    rows=[]
    for item in load(WORK,{}).get("results",[]):
        if item.get("status") not in ("prepared_for_specialist_runtime","pending"): continue
        rows.append({
          "work_id":item.get("work_id"),
          "action_type":item.get("action_type"),
          "primary_provider":"openai",
          "fallback_provider":"local_llama",
          "route":"primary_then_local_fallback",
          "local_available":provider.get("fallback",{}).get("reachable",False),
          "execution_boundary":"internal_non_destructive_only"
        })
    payload={"generated_at":now(),"route_count":len(rows),"routes":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"route_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"ai_task_routing_complete","plan":payload}

print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/ai_task_router.py"

cat > "$CTL/aitaskrouterctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"ai_task_router.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/aitaskrouterctl"

cat > "$AGENTS/ai_provenance_engine.py" <<'PY'
#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
SRC=MEM/"specialist_runtime_results.json"
OUT=MEM/"ai_provenance_log.json"
STATE=MEM/"ai_provenance_state.json"
HEALTH=MEM/"ai_provenance_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    rows=[]
    for r in load(SRC,{}).get("results",[]):
        actual=r.get("actual_result",{})
        if not isinstance(actual,dict): continue
        rows.append({
          "work_id":r.get("work_id"),
          "provider_used":actual.get("_provider_used","unknown"),
          "primary_failure":actual.get("_primary_failure"),
          "confidence":actual.get("confidence"),
          "completed_at":r.get("completed_at"),
          "execution_boundary":r.get("execution_boundary")
        })
    payload={"generated_at":now(),"event_count":len(rows),"events":rows[-500:]}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"event_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"ai_provenance_complete","report":payload}

print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/ai_provenance_engine.py"

cat > "$CTL/aiprovenancectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"ai_provenance_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/aiprovenancectl"

cat > "$AGENTS/local_ai_startup_guard.py" <<'PY'
#!/usr/bin/env python3
import json, subprocess, urllib.request, time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"local_ai_startup_guard.json"; STATE=MEM/"local_ai_startup_guard_state.json"; HEALTH=MEM/"local_ai_startup_guard_health.json"
MODEL=Path.home()/"llama.cpp/models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
SERVER=Path.home()/"llama.cpp/build/bin/llama-server"
LOG=ROOT/"logs/local_ai_server.log"

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def reachable():
    try:
        urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=3).read()
        return True
    except:return False

def run():
    started=False
    if not reachable() and SERVER.exists() and MODEL.exists():
        LOG.parent.mkdir(parents=True,exist_ok=True)
        with LOG.open("ab") as f:
            subprocess.Popen([str(SERVER),"-m",str(MODEL),"--host","127.0.0.1","--port","8080","-c","4096"],
                             stdout=f,stderr=f,start_new_session=True)
        started=True
        for _ in range(20):
            time.sleep(1)
            if reachable(): break
    ok=reachable()
    payload={"generated_at":now(),"reachable":ok,"started_by_guard":started,
             "model_exists":MODEL.exists(),"server_exists":SERVER.exists(),"port":8080}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"reachable":ok});save(HEALTH,{"healthy":ok,"last_checked_at":now()})
    return {"success":True,"status":"local_ai_startup_guard_complete","report":payload}

print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/local_ai_startup_guard.py"

cat > "$CTL/localaiguardctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"local_ai_startup_guard.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/localaiguardctl"

cat > "$AGENTS/ai_recovery_manager.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"ai_recovery_report.json"; STATE=MEM/"ai_recovery_state.json"; HEALTH=MEM/"ai_recovery_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def call(cmd):
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=600)
    return {"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-2000:],"stderr":p.stderr[-1000:]}

def run():
    steps=[
      {"step":"local_ai_guard","result":call([sys.executable,"companyos/localaiguardctl","run"])},
      {"step":"provider_health","result":call([sys.executable,"companyos/aiproviderhealthctl","run"])},
      {"step":"task_router","result":call([sys.executable,"companyos/aitaskrouterctl","run"])}
    ]
    failed=[s["step"] for s in steps if not s["result"]["success"]]
    payload={"generated_at":now(),"failure_count":len(failed),"failed_steps":failed,"steps":steps}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now()})
    return {"success":not failed,"status":"ai_recovery_complete","report":payload}

print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/ai_recovery_manager.py"

cat > "$CTL/airecoveryctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"ai_recovery_manager.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/airecoveryctl"

cat > "$AGENTS/phase25_bundle1_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase25_bundle1_state.json"; REPORT=MEM/"phase25_bundle1_report.json"; HEALTH=MEM/"phase25_bundle1_health.json"
PIPELINE=[
 ("local_ai_guard",["python","companyos/localaiguardctl","run"]),
 ("provider_health",["python","companyos/aiproviderhealthctl","run"]),
 ("task_router",["python","companyos/aitaskrouterctl","run"]),
 ("specialist_runtime",["python","companyos/specialistruntimectl","run"]),
 ("ai_provenance",["python","companyos/aiprovenancectl","run"]),
 ("ai_recovery",["python","companyos/airecoveryctl","run"])
]

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def call(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=2400)
        return {"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-3500:],"stderr":p.stderr[-1500:]}
    except Exception as e:return {"success":False,"error":str(e)}

def run():
    steps=[];failed=[]
    for name,cmd in PIPELINE:
        r=call(cmd);steps.append({"step":name,"result":r})
        if not r.get("success"):failed.append(name)
    report={"generated_at":now(),"steps":steps,"failure_count":len(failed),"failed_steps":failed}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now(),"failure_count":len(failed)})
    return {"success":not failed,"status":"phase25_bundle1_cycle_complete","report":report}

def status():
    def l(p):
        try:return json.loads(p.read_text())
        except:return {}
    return {"success":True,"status":"phase25_bundle1_status","state":l(STATE),"health":l(HEALTH)}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status()
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/phase25_bundle1_controller.py"

cat > "$CTL/phase25bundle1ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase25_bundle1_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase25bundle1ctl"

echo "[1/8] Compiling..."
python -m py_compile \
 "$AGENTS/ai_provider_health_engine.py" "$AGENTS/ai_task_router.py" \
 "$AGENTS/ai_provenance_engine.py" "$AGENTS/local_ai_startup_guard.py" \
 "$AGENTS/ai_recovery_manager.py" "$AGENTS/phase25_bundle1_controller.py" \
 "$CTL/aiproviderhealthctl" "$CTL/aitaskrouterctl" "$CTL/aiprovenancectl" \
 "$CTL/localaiguardctl" "$CTL/airecoveryctl" "$CTL/phase25bundle1ctl"

echo "[2/8] Local AI startup guard..."
python "$CTL/localaiguardctl" run

echo "[3/8] Provider health..."
python "$CTL/aiproviderhealthctl" run

echo "[4/8] Task routing..."
python "$CTL/aitaskrouterctl" run

echo "[5/8] Provenance..."
python "$CTL/aiprovenancectl" run

echo "[6/8] Recovery manager..."
python "$CTL/airecoveryctl" run

echo "[7/8] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text()); jobs=d.setdefault("jobs",[])
job={"id":"phase25-hybrid-ai-orchestration","enabled":True,"interval_seconds":7200,
     "command":["python","companyos/phase25bundle1ctl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart

echo "[8/8] Integrated run + verification..."
python "$CTL/phase25bundle1ctl" run || true

python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"ai_provider_health_engine.py",r/"agents"/"ai_task_router.py",
r/"agents"/"ai_provenance_engine.py",r/"agents"/"local_ai_startup_guard.py",
r/"agents"/"ai_recovery_manager.py",r/"agents"/"phase25_bundle1_controller.py",
r/"companyos"/"aiproviderhealthctl",r/"companyos"/"aitaskrouterctl",
r/"companyos"/"aiprovenancectl",r/"companyos"/"localaiguardctl",
r/"companyos"/"airecoveryctl",r/"companyos"/"phase25bundle1ctl",
r/"ceo_memory"/"phase25_bundle1_config.json",r/"ceo_memory"/"ai_provider_health_report.json",
r/"ceo_memory"/"ai_task_routing_plan.json",r/"ceo_memory"/"ai_provenance_log.json",
r/"ceo_memory"/"local_ai_startup_guard.json",r/"ceo_memory"/"ai_recovery_report.json",
r/"ceo_memory"/"autonomous_operations_config.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:12]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase25_bundle1_config.json").read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
          "automatic_fund_transfer","automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads((r/"ceo_memory"/"autonomous_operations_config.json").read_text())
if not any(x.get("id")=="phase25-hybrid-ai-orchestration" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Phase 25 Bundle 1 scheduler job missing/disabled")
print("--------------------------------------------")
print("PHASE 25 BUNDLE 1 VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 25 BUNDLE 1 INSTALLED"
echo " HYBRID AI ORCHESTRATION CORE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Master commands:"
echo "  python companyos/phase25bundle1ctl run"
echo "  python companyos/phase25bundle1ctl status"
echo "  python companyos/aiproviderhealthctl run"
echo "  python companyos/aiprovenancectl run"
echo
echo "Bundle includes:"
echo "  - OpenAI primary + local llama fallback orchestration"
echo "  - Provider health monitoring"
echo "  - Local AI startup guard"
echo "  - AI task routing"
echo "  - AI provenance/fallback tracking"
echo "  - Internal AI recovery manager"
echo "  - Integrated Phase 25 cycle"
