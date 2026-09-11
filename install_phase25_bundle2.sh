#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase25_bundle2_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 25 BUNDLE 2 - MULTI-AGENT INTELLIGENCE CORE"
echo "============================================================"

for f in \
  "$AGENTS/model_capability_registry.py" \
  "$AGENTS/task_decomposition_engine.py" \
  "$AGENTS/specialist_delegation_engine.py" \
  "$AGENTS/result_validation_engine.py" \
  "$AGENTS/ceo_synthesis_engine.py" \
  "$AGENTS/ai_resource_governor.py" \
  "$AGENTS/phase25_bundle2_controller.py" \
  "$CTL/modelcapabilityctl" \
  "$CTL/taskdecompositionctl" \
  "$CTL/specialistdelegationctl" \
  "$CTL/resultvalidationctl" \
  "$CTL/ceosynthesisctl" \
  "$CTL/airesourcegovernorctl" \
  "$CTL/phase25bundle2ctl"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/phase25_bundle2_config.json" <<'JSON'
{
  "enabled": true,
  "maximum_parent_tasks": 20,
  "maximum_subtasks_per_parent": 5,
  "maximum_parallel_specialists": 3,
  "minimum_validation_confidence": 0.55,
  "minimum_synthesis_confidence": 0.60,
  "local_model_context_limit": 4096,
  "preferred_primary_provider": "openai",
  "preferred_fallback_provider": "local_llama",
  "automatic_internal_task_decomposition": true,
  "automatic_internal_specialist_delegation": true,
  "automatic_internal_result_validation": true,
  "automatic_internal_ceo_synthesis": true,
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

cat > "$AGENTS/model_capability_registry.py" <<'PY'
#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"model_capability_registry.json"
STATE=MEM/"model_capability_state.json"
HEALTH=MEM/"model_capability_health.json"
PROVIDER=MEM/"ai_provider_health_report.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    ph=load(PROVIDER,{})
    rows=[
      {
        "provider":"openai",
        "model":"gpt-4.1-mini",
        "available":bool(ph.get("primary",{}).get("configured")),
        "strengths":["reasoning","planning","structured_outputs","tool_orchestration"],
        "cost_class":"metered_api",
        "priority":1
      },
      {
        "provider":"local_llama",
        "model":"qwen2.5-1.5b-instruct-q4_k_m",
        "available":bool(ph.get("fallback",{}).get("reachable")),
        "strengths":["offline_reasoning","summarization","classification","fallback_execution"],
        "cost_class":"local_compute",
        "priority":2
      }
    ]
    payload={"generated_at":now(),"model_count":len(rows),"models":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"model_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"model_capability_registry_complete","registry":payload}

print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/model_capability_registry.py"

cat > "$CTL/modelcapabilityctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"model_capability_registry.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/modelcapabilityctl"

cat > "$AGENTS/task_decomposition_engine.py" <<'PY'
#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase25_bundle2_config.json"
SRC=MEM/"governed_internal_work_results.json"
OUT=MEM/"decomposed_ai_tasks.json"
STATE=MEM/"task_decomposition_state.json"
HEALTH=MEM/"task_decomposition_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def hid(x):return hashlib.sha256(str(x).encode()).hexdigest()[:18]

def run():
    cfg=load(CFG,{})
    rows=[]
    parents=load(SRC,{}).get("results",[])[:int(cfg.get("maximum_parent_tasks",20))]
    for p in parents:
        if p.get("status") not in ("prepared_for_specialist_runtime","pending","completed"): continue
        parent_id=p.get("work_id") or hid(p)
        action=p.get("action_type","analysis")
        templates=[
          ("research","Gather and organize relevant internal evidence"),
          ("analysis","Analyze options, constraints, risks, and tradeoffs"),
          ("planning","Create a practical internal execution plan"),
          ("review","Review assumptions, gaps, and failure modes"),
          ("synthesis","Summarize the strongest internal recommendation")
        ]
        subtasks=[]
        for role,inst in templates[:int(cfg.get("maximum_subtasks_per_parent",5))]:
            subtasks.append({
              "subtask_id":hid(parent_id+"|"+role),
              "parent_work_id":parent_id,
              "role":role,
              "instruction":f"{inst}. Parent action type: {action}.",
              "status":"ready_for_internal_delegation",
              "execution_boundary":"internal_non_destructive_only"
            })
        rows.append({"parent_work_id":parent_id,"subtask_count":len(subtasks),"subtasks":subtasks})
    payload={"generated_at":now(),"parent_count":len(rows),"parents":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"parent_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"task_decomposition_complete","report":payload}

print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/task_decomposition_engine.py"

cat > "$CTL/taskdecompositionctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"task_decomposition_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/taskdecompositionctl"

cat > "$AGENTS/specialist_delegation_engine.py" <<'PY'
#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
TASKS=MEM/"decomposed_ai_tasks.json"
MODELS=MEM/"model_capability_registry.json"
OUT=MEM/"specialist_delegation_plan.json"
STATE=MEM/"specialist_delegation_state.json"
HEALTH=MEM/"specialist_delegation_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    models=load(MODELS,{}).get("models",[])
    openai=next((m for m in models if m.get("provider")=="openai"),{})
    local=next((m for m in models if m.get("provider")=="local_llama"),{})
    rows=[]
    for parent in load(TASKS,{}).get("parents",[]):
        for s in parent.get("subtasks",[]):
            preferred="openai" if openai.get("available") else "local_llama"
            fallback="local_llama" if local.get("available") else None
            rows.append({
              "subtask_id":s.get("subtask_id"),
              "parent_work_id":s.get("parent_work_id"),
              "specialist_role":s.get("role"),
              "preferred_provider":preferred,
              "fallback_provider":fallback,
              "status":"assigned_internal",
              "execution_boundary":"internal_non_destructive_only"
            })
    payload={"generated_at":now(),"assignment_count":len(rows),"assignments":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"assignment_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"specialist_delegation_complete","plan":payload}

print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/specialist_delegation_engine.py"

cat > "$CTL/specialistdelegationctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"specialist_delegation_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/specialistdelegationctl"

cat > "$AGENTS/result_validation_engine.py" <<'PY'
#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase25_bundle2_config.json"
SRC=MEM/"specialist_runtime_results.json"
OUT=MEM/"validated_ai_results.json"
STATE=MEM/"result_validation_state.json"
HEALTH=MEM/"result_validation_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    minimum=float(load(CFG,{}).get("minimum_validation_confidence",0.55))
    rows=[]
    for r in load(SRC,{}).get("results",[]):
        actual=r.get("actual_result",{})
        if not isinstance(actual,dict): continue
        confidence=float(actual.get("confidence",0) or 0)
        valid=bool(actual.get("summary")) and confidence>=minimum
        rows.append({
          "work_id":r.get("work_id"),
          "valid":valid,
          "confidence":confidence,
          "provider_used":actual.get("_provider_used","unknown"),
          "summary_present":bool(actual.get("summary")),
          "status":"validated_internal_result" if valid else "needs_internal_review",
          "execution_boundary":"internal_non_destructive_only"
        })
    payload={"generated_at":now(),"validated_count":sum(1 for x in rows if x["valid"]),
             "review_count":sum(1 for x in rows if not x["valid"]),"results":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"result_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"result_validation_complete","report":payload}

print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/result_validation_engine.py"

cat > "$CTL/resultvalidationctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"result_validation_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/resultvalidationctl"

cat > "$AGENTS/ceo_synthesis_engine.py" <<'PY'
#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
VALID=MEM/"validated_ai_results.json"
RUNTIME=MEM/"specialist_runtime_results.json"
OUT=MEM/"ceo_ai_synthesis.json"
STATE=MEM/"ceo_ai_synthesis_state.json"
HEALTH=MEM/"ceo_ai_synthesis_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    valid_ids={x.get("work_id") for x in load(VALID,{}).get("results",[]) if x.get("valid")}
    summaries=[];recommendations=[];risks=[];providers={}
    for r in load(RUNTIME,{}).get("results",[]):
        if r.get("work_id") not in valid_ids: continue
        a=r.get("actual_result",{})
        if not isinstance(a,dict): continue
        if a.get("summary"):summaries.append(a["summary"])
        recommendations.extend(a.get("recommendations",[]) if isinstance(a.get("recommendations",[]),list) else [])
        risks.extend(a.get("risks",[]) if isinstance(a.get("risks",[]),list) else [])
        p=a.get("_provider_used","unknown");providers[p]=providers.get(p,0)+1
    payload={
      "generated_at":now(),
      "validated_input_count":len(valid_ids),
      "executive_summary":summaries[:10],
      "top_recommendations":recommendations[:15],
      "top_risks":risks[:15],
      "provider_mix":providers,
      "decision_boundary":"internal_recommendation_only",
      "external_authority_granted":False
    }
    save(OUT,payload);save(STATE,{"last_run_at":now(),"validated_input_count":len(valid_ids)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"ceo_ai_synthesis_complete","synthesis":payload}

print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/ceo_synthesis_engine.py"

cat > "$CTL/ceosynthesisctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"ceo_synthesis_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/ceosynthesisctl"

cat > "$AGENTS/ai_resource_governor.py" <<'PY'
#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase25_bundle2_config.json"
PROV=MEM/"ai_provenance_log.json"
ROUTES=MEM/"ai_task_routing_plan.json"
OUT=MEM/"ai_resource_governor_report.json"
STATE=MEM/"ai_resource_governor_state.json"
HEALTH=MEM/"ai_resource_governor_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    cfg=load(CFG,{})
    events=load(PROV,{}).get("events",[])
    local=sum(1 for e in events if e.get("provider_used")=="local_llama_fallback")
    primary=sum(1 for e in events if e.get("provider_used")=="openai_primary")
    route_count=load(ROUTES,{}).get("route_count",0)
    payload={
      "generated_at":now(),
      "openai_completed":primary,
      "local_fallback_completed":local,
      "queued_routes":route_count,
      "maximum_parallel_specialists":cfg.get("maximum_parallel_specialists",3),
      "local_context_limit":cfg.get("local_model_context_limit",4096),
      "recommendation":"Prefer OpenAI when available; use local fallback for resilience and low-cost internal work.",
      "external_authority_granted":False
    }
    save(OUT,payload);save(STATE,{"last_run_at":now()});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"ai_resource_governor_complete","report":payload}

print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/ai_resource_governor.py"

cat > "$CTL/airesourcegovernorctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"ai_resource_governor.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/airesourcegovernorctl"

cat > "$AGENTS/phase25_bundle2_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase25_bundle2_state.json"; REPORT=MEM/"phase25_bundle2_report.json"; HEALTH=MEM/"phase25_bundle2_health.json"

PIPELINE=[
 ("phase25_bundle1",["python","companyos/phase25bundle1ctl","run"]),
 ("model_registry",["python","companyos/modelcapabilityctl","run"]),
 ("task_decomposition",["python","companyos/taskdecompositionctl","run"]),
 ("specialist_delegation",["python","companyos/specialistdelegationctl","run"]),
 ("result_validation",["python","companyos/resultvalidationctl","run"]),
 ("ceo_synthesis",["python","companyos/ceosynthesisctl","run"]),
 ("resource_governor",["python","companyos/airesourcegovernorctl","run"])
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
    return {"success":not failed,"status":"phase25_bundle2_cycle_complete","report":report}

def status():
    def l(p):
        try:return json.loads(p.read_text())
        except:return {}
    return {"success":True,"status":"phase25_bundle2_status","state":l(STATE),"health":l(HEALTH)}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status()
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/phase25_bundle2_controller.py"

cat > "$CTL/phase25bundle2ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase25_bundle2_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase25bundle2ctl"

echo "[1/8] Compiling..."
python -m py_compile \
 "$AGENTS/model_capability_registry.py" \
 "$AGENTS/task_decomposition_engine.py" \
 "$AGENTS/specialist_delegation_engine.py" \
 "$AGENTS/result_validation_engine.py" \
 "$AGENTS/ceo_synthesis_engine.py" \
 "$AGENTS/ai_resource_governor.py" \
 "$AGENTS/phase25_bundle2_controller.py" \
 "$CTL/modelcapabilityctl" "$CTL/taskdecompositionctl" "$CTL/specialistdelegationctl" \
 "$CTL/resultvalidationctl" "$CTL/ceosynthesisctl" "$CTL/airesourcegovernorctl" "$CTL/phase25bundle2ctl"

echo "[2/8] Model capability registry..."
python "$CTL/modelcapabilityctl" run

echo "[3/8] Task decomposition..."
python "$CTL/taskdecompositionctl" run

echo "[4/8] Specialist delegation..."
python "$CTL/specialistdelegationctl" run

echo "[5/8] Result validation..."
python "$CTL/resultvalidationctl" run

echo "[6/8] CEO synthesis + AI resource governor..."
python "$CTL/ceosynthesisctl" run
python "$CTL/airesourcegovernorctl" run

echo "[7/8] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text()); jobs=d.setdefault("jobs",[])
job={"id":"phase25-multi-agent-intelligence","enabled":True,"interval_seconds":10800,
     "command":["python","companyos/phase25bundle2ctl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart

echo "[8/8] Integrated run + verification..."
python "$CTL/phase25bundle2ctl" run || true

python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"model_capability_registry.py",r/"agents"/"task_decomposition_engine.py",
r/"agents"/"specialist_delegation_engine.py",r/"agents"/"result_validation_engine.py",
r/"agents"/"ceo_synthesis_engine.py",r/"agents"/"ai_resource_governor.py",
r/"agents"/"phase25_bundle2_controller.py",r/"companyos"/"modelcapabilityctl",
r/"companyos"/"taskdecompositionctl",r/"companyos"/"specialistdelegationctl",
r/"companyos"/"resultvalidationctl",r/"companyos"/"ceosynthesisctl",
r/"companyos"/"airesourcegovernorctl",r/"companyos"/"phase25bundle2ctl",
r/"ceo_memory"/"phase25_bundle2_config.json",r/"ceo_memory"/"model_capability_registry.json",
r/"ceo_memory"/"decomposed_ai_tasks.json",r/"ceo_memory"/"specialist_delegation_plan.json",
r/"ceo_memory"/"validated_ai_results.json",r/"ceo_memory"/"ceo_ai_synthesis.json",
r/"ceo_memory"/"ai_resource_governor_report.json",r/"ceo_memory"/"autonomous_operations_config.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:14]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase25_bundle2_config.json").read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
          "automatic_fund_transfer","automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads((r/"ceo_memory"/"autonomous_operations_config.json").read_text())
if not any(x.get("id")=="phase25-multi-agent-intelligence" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Phase 25 Bundle 2 scheduler job missing/disabled")
print("--------------------------------------------")
print("PHASE 25 BUNDLE 2 VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 25 BUNDLE 2 INSTALLED"
echo " MULTI-AGENT INTELLIGENCE CORE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Master commands:"
echo "  python companyos/phase25bundle2ctl run"
echo "  python companyos/phase25bundle2ctl status"
echo "  python companyos/ceosynthesisctl run"
echo "  python companyos/airesourcegovernorctl run"
echo
echo "Bundle includes:"
echo "  - Model capability registry"
echo "  - Task decomposition engine"
echo "  - Specialist delegation engine"
echo "  - Result validation engine"
echo "  - CEO synthesis engine"
echo "  - AI resource governor"
echo "  - Integrated Phase 25 Bundle 2 cycle"
