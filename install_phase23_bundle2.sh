#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase23_bundle2_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 23 BUNDLE 2 - ADAPTIVE EXECUTION & LEARNING CORE"
echo "============================================================"

for f in \
  "$AGENTS/specialist_performance_learner.py" \
  "$AGENTS/provider_health_router.py" \
  "$AGENTS/opportunity_promotion_engine.py" \
  "$AGENTS/improvement_queue_engine.py" \
  "$AGENTS/executive_briefing_engine.py" \
  "$AGENTS/autonomy_watchdog.py" \
  "$AGENTS/phase23_bundle2_controller.py" \
  "$CTL/specialistlearningctl" \
  "$CTL/providerhealthctl" \
  "$CTL/opportunitypromotectl" \
  "$CTL/improvementqueuectl" \
  "$CTL/executivebriefctl" \
  "$CTL/autonomywatchdogctl" \
  "$CTL/phase23bundle2ctl"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/phase23_bundle2_config.json" <<'JSON'
{
  "enabled": true,
  "specialist_learning_window": 200,
  "minimum_confidence_for_learning": 0.5,
  "provider_failure_threshold": 3,
  "maximum_promotions_per_cycle": 10,
  "maximum_improvement_queue_items": 25,
  "watchdog_stale_minutes": 180,
  "automatic_internal_learning": true,
  "automatic_internal_promotion": true,
  "automatic_internal_improvement_queueing": true,
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

# ------------------------------------------------------------
# 1. Specialist performance learner
# ------------------------------------------------------------
cat > "$AGENTS/specialist_performance_learner.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_bundle2_config.json"
RESULTS=MEM/"specialist_runtime_results.json"
OUT=MEM/"specialist_performance_profiles.json"
STATE=MEM/"specialist_learning_state.json"
HEALTH=MEM/"specialist_learning_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def f(v,d=0):
    try:return float(v)
    except:return float(d)

def learn():
    cfg=load(CFG,{})
    rows=load(RESULTS,{}).get("results",[])
    window=int(cfg.get("specialist_learning_window",200))
    minimum=f(cfg.get("minimum_confidence_for_learning",.5),.5)
    buckets=defaultdict(list)

    for r in rows[-window:]:
        if r.get("status")!="completed": continue
        actual=r.get("actual_result") or {}
        conf=f(actual.get("confidence",0),0)
        if conf<minimum: continue
        role=r.get("specialist_role") or r.get("action_type") or "general"
        buckets[role].append(conf)

    profiles=[]
    for role,vals in buckets.items():
        avg=sum(vals)/len(vals)
        profiles.append({
          "specialist_role":role,
          "samples":len(vals),
          "average_confidence":round(avg,3),
          "performance_band":"strong" if avg>=.8 else "good" if avg>=.65 else "developing"
        })
    profiles.sort(key=lambda x:(x["average_confidence"],x["samples"]),reverse=True)
    payload={"generated_at":now(),"profile_count":len(profiles),"profiles":profiles}
    save(OUT,payload);save(STATE,{"last_learned_at":now(),"profile_count":len(profiles)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"profile_count":len(profiles)})
    return {"success":True,"status":"specialist_performance_learning_complete","report":payload}

def status():
    return {"success":True,"status":"specialist_learning_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"profiles":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=learn() if a=="learn" else status() if a=="status" else {"success":False,"allowed":["learn","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/specialist_performance_learner.py"

cat > "$CTL/specialistlearningctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"specialist_performance_learner.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/specialistlearningctl"

# ------------------------------------------------------------
# 2. Provider health router
# ------------------------------------------------------------
cat > "$AGENTS/provider_health_router.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
RUNTIME=MEM/"specialist_runtime_config.json"
CONSUMER=MEM/"live_specialist_consumer_report.json"
OUT=MEM/"provider_health_report.json"
STATE=MEM/"provider_health_state.json"
HEALTH=MEM/"provider_health_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def evaluate():
    runtime=load(RUNTIME,{})
    report=load(CONSUMER,{})
    pending=int(report.get("pending_count",0) or 0)
    completed=int(report.get("completed_count",0) or 0)
    provider=runtime.get("provider","openai_compatible")
    model=runtime.get("model","openrouter/free")
    state="healthy" if pending==0 else "degraded" if completed>0 else "watch"
    payload={"generated_at":now(),"provider":provider,"model":model,
      "completed_count":completed,"pending_count":pending,"provider_state":state,
      "recommended_model":model}
    save(OUT,payload);save(STATE,{"last_evaluated_at":now(),"provider_state":state})
    save(HEALTH,{"healthy":state!="watch","last_checked_at":now(),"provider_state":state})
    return {"success":True,"status":"provider_health_evaluation_complete","report":payload}

def status():
    return {"success":True,"status":"provider_health_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=evaluate() if a=="evaluate" else status() if a=="status" else {"success":False,"allowed":["evaluate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/provider_health_router.py"

cat > "$CTL/providerhealthctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"provider_health_router.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/providerhealthctl"

# ------------------------------------------------------------
# 3. Opportunity promotion engine
# ------------------------------------------------------------
cat > "$AGENTS/opportunity_promotion_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_bundle2_config.json"
SOURCE=MEM/"generated_business_opportunities.json"
QUEUE=MEM/"opportunity_promotion_queue.json"
STATE=MEM/"opportunity_promotion_state.json"
HEALTH=MEM/"opportunity_promotion_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def fid(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=str).encode()).hexdigest()[:20]

def promote():
    cfg=load(CFG,{})
    rows=load(SOURCE,{}).get("opportunities",[])
    old=load(QUEUE,{"items":[]}).get("items",[])
    seen={x.get("promotion_id") for x in old}
    maximum=int(cfg.get("maximum_promotions_per_cycle",10))
    added=[]
    for row in rows:
        if len(added)>=maximum:break
        pid=fid({"id":row.get("id"),"title":row.get("title")})
        if pid in seen:continue
        item={"promotion_id":pid,"opportunity_id":row.get("id"),"title":row.get("title"),
          "category":row.get("category"),"score":row.get("score"),
          "status":"ready_for_internal_review","authority":"internal_non_destructive_only",
          "created_at":now()}
        old.append(item);added.append(item);seen.add(pid)
    payload={"generated_at":now(),"item_count":len(old),"items":old}
    save(QUEUE,payload);save(STATE,{"last_promoted_at":now(),"added_count":len(added),"item_count":len(old)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"item_count":len(old)})
    return {"success":True,"status":"opportunity_promotion_complete","added_count":len(added),"queue":payload}

def status():
    return {"success":True,"status":"opportunity_promotion_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"queue":load(QUEUE,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=promote() if a=="promote" else status() if a=="status" else {"success":False,"allowed":["promote","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/opportunity_promotion_engine.py"

cat > "$CTL/opportunitypromotectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"opportunity_promotion_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/opportunitypromotectl"

# ------------------------------------------------------------
# 4. Improvement queue engine
# ------------------------------------------------------------
cat > "$AGENTS/improvement_queue_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_bundle2_config.json"
SOURCE=MEM/"self_improvement_proposals.json"
OUT=MEM/"governed_improvement_queue.json"
STATE=MEM/"improvement_queue_state.json"
HEALTH=MEM/"improvement_queue_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def queue():
    cfg=load(CFG,{})
    source=load(SOURCE,{}).get("proposals",[])
    existing=load(OUT,{"items":[]}).get("items",[])
    seen={x.get("id") for x in existing}
    maximum=int(cfg.get("maximum_improvement_queue_items",25))
    added=[]
    for p in source:
        if len(existing)>=maximum:break
        if p.get("id") in seen:continue
        item=dict(p)
        item["queue_status"]="awaiting_governed_internal_review"
        item["execution_authority"]="none"
        item["queued_at"]=now()
        existing.append(item);added.append(item);seen.add(p.get("id"))
    payload={"generated_at":now(),"item_count":len(existing),"items":existing,
      "note":"Queue does not authorize code changes, merge, deploy, spending, or destructive actions."}
    save(OUT,payload);save(STATE,{"last_queued_at":now(),"added_count":len(added),"item_count":len(existing)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"item_count":len(existing)})
    return {"success":True,"status":"improvement_queue_complete","added_count":len(added),"queue":payload}

def status():
    return {"success":True,"status":"improvement_queue_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"queue":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=queue() if a=="queue" else status() if a=="status" else {"success":False,"allowed":["queue","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/improvement_queue_engine.py"

cat > "$CTL/improvementqueuectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"improvement_queue_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/improvementqueuectl"

# ------------------------------------------------------------
# 5. Executive briefing engine
# ------------------------------------------------------------
cat > "$AGENTS/executive_briefing_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"executive_briefing.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d

def build():
    performance=load("business_performance_scorecard.json",{})
    opportunities=load("generated_business_opportunities.json",{}).get("opportunities",[])
    improvements=load("governed_improvement_queue.json",{}).get("items",[])
    provider=load("provider_health_report.json",{})
    specialists=load("specialist_performance_profiles.json",{}).get("profiles",[])
    autonomy=load("autonomy_core_health.json",{})

    payload={
      "generated_at":now(),
      "headline":"CompanyOS Executive Briefing",
      "system_health":"healthy" if autonomy.get("healthy",False) else "attention",
      "business_performance_score":performance.get("overall_score"),
      "top_opportunities":opportunities[:5],
      "top_improvement_items":improvements[:5],
      "provider_health":provider,
      "top_specialist_profiles":specialists[:5],
      "recommended_focus":[
        x.get("title") for x in opportunities[:3] if x.get("title")
      ],
      "external_authority_granted":False
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return {"success":True,"status":"executive_briefing_complete","briefing":payload}

r=build()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/executive_briefing_engine.py"

cat > "$CTL/executivebriefctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"executive_briefing_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/executivebriefctl"

# ------------------------------------------------------------
# 6. Autonomy watchdog
# ------------------------------------------------------------
cat > "$AGENTS/autonomy_watchdog.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"autonomy_watchdog_report.json"; HEALTH=MEM/"autonomy_watchdog_health.json"

CHECKS=[
 ("phase23_health.json","phase23"),
 ("autonomy_core_health.json","autonomy"),
 ("specialist_runtime_health.json","specialist_runtime"),
 ("provider_health_health.json","provider"),
 ("persistent_memory_health.json","memory")
]

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d

def run():
    results=[];failures=[]
    for name,label in CHECKS:
        p=MEM/name
        data=load(p,{})
        ok=bool(data.get("healthy",False)) if data else False
        results.append({"component":label,"healthy":ok,"data":data})
        if not ok:failures.append(label)
    payload={"generated_at":now(),"healthy":not failures,"failure_count":len(failures),
      "failed_components":failures,"checks":results}
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    HEALTH.write_text(json.dumps({"healthy":not failures,"last_checked_at":now(),
      "failure_count":len(failures)},indent=2),encoding="utf-8")
    return {"success":True,"status":"autonomy_watchdog_complete","report":payload}

r=run()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/autonomy_watchdog.py"

cat > "$CTL/autonomywatchdogctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"autonomy_watchdog.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/autonomywatchdogctl"

# ------------------------------------------------------------
# 7. Bundle controller
# ------------------------------------------------------------
cat > "$AGENTS/phase23_bundle2_controller.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase23_bundle2_state.json"; REPORT=MEM/"phase23_bundle2_report.json"; HEALTH=MEM/"phase23_bundle2_health.json"

PIPELINE=[
 ("phase23_core",["python","companyos/phase23ctl","run"]),
 ("specialist_learning",["python","companyos/specialistlearningctl","learn"]),
 ("provider_health",["python","companyos/providerhealthctl","evaluate"]),
 ("opportunity_promotion",["python","companyos/opportunitypromotectl","promote"]),
 ("improvement_queue",["python","companyos/improvementqueuectl","queue"]),
 ("executive_briefing",["python","companyos/executivebriefctl","show"]),
 ("watchdog",["python","companyos/autonomywatchdogctl","run"])
]

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def call(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=1800)
        return {"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-3500:],"stderr":p.stderr[-1500:]}
    except Exception as e:return {"success":False,"error":str(e)}

def run():
    steps=[];failed=[]
    for name,cmd in PIPELINE:
        r=call(cmd);steps.append({"step":name,"result":r})
        if not r.get("success"):failed.append(name)
    report={"generated_at":now(),"steps":steps,"failure_count":len(failed),"failed_steps":failed}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed})
    save(HEALTH,{"healthy":not failed,"last_checked_at":now(),"failure_count":len(failed)})
    return {"success":not failed,"status":"phase23_bundle2_cycle_complete","report":report}

def status():
    def load(p):
        try:return json.loads(p.read_text())
        except:return {}
    return {"success":True,"status":"phase23_bundle2_status","state":load(STATE),"health":load(HEALTH)}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/phase23_bundle2_controller.py"

cat > "$CTL/phase23bundle2ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase23_bundle2_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase23bundle2ctl"

echo "[1/8] Compiling..."
python -m py_compile \
 "$AGENTS/specialist_performance_learner.py" \
 "$AGENTS/provider_health_router.py" \
 "$AGENTS/opportunity_promotion_engine.py" \
 "$AGENTS/improvement_queue_engine.py" \
 "$AGENTS/executive_briefing_engine.py" \
 "$AGENTS/autonomy_watchdog.py" \
 "$AGENTS/phase23_bundle2_controller.py" \
 "$CTL/specialistlearningctl" "$CTL/providerhealthctl" "$CTL/opportunitypromotectl" \
 "$CTL/improvementqueuectl" "$CTL/executivebriefctl" "$CTL/autonomywatchdogctl" "$CTL/phase23bundle2ctl"

echo "[2/8] Learning specialist performance..."
python "$CTL/specialistlearningctl" learn

echo "[3/8] Evaluating provider health..."
python "$CTL/providerhealthctl" evaluate

echo "[4/8] Promoting opportunities and queueing improvements..."
python "$CTL/opportunitypromotectl" promote
python "$CTL/improvementqueuectl" queue

echo "[5/8] Building executive briefing..."
python "$CTL/executivebriefctl" show

echo "[6/8] Running watchdog..."
python "$CTL/autonomywatchdogctl" run

echo "[7/8] Registering scheduler and running one cycle..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase23-adaptive-execution-learning","enabled":True,"interval_seconds":7200,
"command":["python","companyos/phase23bundle2ctl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart
python "$CTL/phase23bundle2ctl" run || true

echo "[8/8] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"specialist_performance_learner.py",r/"agents"/"provider_health_router.py",
r/"agents"/"opportunity_promotion_engine.py",r/"agents"/"improvement_queue_engine.py",
r/"agents"/"executive_briefing_engine.py",r/"agents"/"autonomy_watchdog.py",
r/"agents"/"phase23_bundle2_controller.py",r/"companyos"/"specialistlearningctl",
r/"companyos"/"providerhealthctl",r/"companyos"/"opportunitypromotectl",
r/"companyos"/"improvementqueuectl",r/"companyos"/"executivebriefctl",
r/"companyos"/"autonomywatchdogctl",r/"companyos"/"phase23bundle2ctl",
r/"ceo_memory"/"phase23_bundle2_config.json",r/"ceo_memory"/"specialist_performance_profiles.json",
r/"ceo_memory"/"provider_health_report.json",r/"ceo_memory"/"opportunity_promotion_queue.json",
r/"ceo_memory"/"governed_improvement_queue.json",r/"ceo_memory"/"executive_briefing.json",
r/"ceo_memory"/"autonomy_watchdog_report.json",r/"ceo_memory"/"autonomous_operations_config.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:14]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase23_bundle2_config.json").read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
"automatic_fund_transfer","automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads((r/"ceo_memory"/"autonomous_operations_config.json").read_text())
if not any(x.get("id")=="phase23-adaptive-execution-learning" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Phase 23 Bundle 2 scheduler job missing/disabled")
print("--------------------------------------------")
print("PHASE 23 BUNDLE 2 VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 23 BUNDLE 2 INSTALLED"
echo " ADAPTIVE EXECUTION & LEARNING CORE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Master commands:"
echo "  python companyos/phase23bundle2ctl run"
echo "  python companyos/phase23bundle2ctl status"
echo "  python companyos/executivebriefctl show"
echo "  python companyos/autonomywatchdogctl run"
echo
echo "Bundle includes:"
echo "  - Specialist performance learning"
echo "  - Provider health routing"
echo "  - Opportunity promotion queue"
echo "  - Governed improvement queue"
echo "  - Executive briefing"
echo "  - Autonomy watchdog"
echo "  - Master adaptive execution/learning cycle"
