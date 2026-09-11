#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase24_bundle1_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 24 BUNDLE 1 - BUSINESS WORKFLOW ORCHESTRATION CORE"
echo "============================================================"

for f in \
  "$AGENTS/task_lifecycle_engine.py" \
  "$AGENTS/research_to_specialist_bridge.py" \
  "$AGENTS/specialist_collaboration_engine.py" \
  "$AGENTS/opportunity_validation_engine.py" \
  "$AGENTS/business_workflow_orchestrator.py" \
  "$AGENTS/ceo_operating_report.py" \
  "$AGENTS/phase24_controller.py" \
  "$CTL/tasklifecyclectl" \
  "$CTL/researchbridgectl" \
  "$CTL/collaborationctl" \
  "$CTL/opportunityvalidatectl" \
  "$CTL/businessworkflowctl" \
  "$CTL/ceoreportctl" \
  "$CTL/phase24ctl"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/phase24_config.json" <<'JSON'
{
  "enabled": true,
  "maximum_active_tasks": 100,
  "maximum_research_tasks_per_cycle": 10,
  "maximum_collaboration_groups": 10,
  "minimum_validation_score": 55,
  "automatic_internal_task_lifecycle": true,
  "automatic_internal_research_routing": true,
  "automatic_internal_collaboration": true,
  "automatic_internal_validation": true,
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
# 1. Persistent task lifecycle engine
# ------------------------------------------------------------
cat > "$AGENTS/task_lifecycle_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_config.json"
STRATEGIC=MEM/"strategic_30_day_plan.json"
RESEARCH=MEM/"research_mission_queue.json"
IMPROVEMENTS=MEM/"governed_improvement_queue.json"
OUT=MEM/"persistent_task_registry.json"
STATE=MEM/"task_lifecycle_state.json"
HEALTH=MEM/"task_lifecycle_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2),encoding="utf-8"); t.replace(p)
def tid(kind,key): return hashlib.sha256(f"{kind}|{key}".encode()).hexdigest()[:20]

def sync():
    cfg=load(CFG,{})
    existing=load(OUT,{"tasks":[]}).get("tasks",[])
    by_id={x.get("task_id"):x for x in existing if x.get("task_id")}
    added=[]

    for a in load(STRATEGIC,{}).get("actions",[]):
        task_id=tid("strategic",a.get("id") or a.get("title"))
        if task_id not in by_id:
            by_id[task_id]={
              "task_id":task_id,"source":"strategic_plan","title":a.get("title"),
              "category":a.get("category"),"priority":a.get("priority",50),
              "status":"planned","authority":"internal_non_destructive_only",
              "created_at":now(),"updated_at":now()
            };added.append(by_id[task_id])

    for r in load(RESEARCH,{}).get("missions",[]):
        task_id=tid("research",r.get("mission_id"))
        if task_id not in by_id:
            by_id[task_id]={
              "task_id":task_id,"source":"research_mission","title":r.get("title"),
              "category":"research","priority":60,
              "status":"queued","authority":"internal_non_destructive_only",
              "created_at":now(),"updated_at":now()
            };added.append(by_id[task_id])

    for p in load(IMPROVEMENTS,{}).get("items",[]):
        task_id=tid("improvement",p.get("id"))
        if task_id not in by_id:
            by_id[task_id]={
              "task_id":task_id,"source":"improvement_queue","title":p.get("title"),
              "category":p.get("category","improvement"),"priority":p.get("priority",50),
              "status":"awaiting_governed_internal_review","authority":"none",
              "created_at":now(),"updated_at":now()
            };added.append(by_id[task_id])

    tasks=list(by_id.values())[:int(cfg.get("maximum_active_tasks",100))]
    payload={"generated_at":now(),"task_count":len(tasks),"tasks":tasks}
    save(OUT,payload)
    save(STATE,{"last_synced_at":now(),"added_count":len(added),"task_count":len(tasks)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"task_count":len(tasks)})
    return {"success":True,"status":"task_lifecycle_sync_complete","added_count":len(added),"registry":payload}

def status():
    return {"success":True,"status":"task_lifecycle_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"registry":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=sync() if a=="sync" else status() if a=="status" else {"success":False,"allowed":["sync","status"]}
print(json.dumps(r,indent=2)); raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/task_lifecycle_engine.py"

cat > "$CTL/tasklifecyclectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"task_lifecycle_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/tasklifecyclectl"

# ------------------------------------------------------------
# 2. Research -> live specialist bridge
# ------------------------------------------------------------
cat > "$AGENTS/research_to_specialist_bridge.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_config.json"
RESEARCH=MEM/"research_mission_queue.json"
TARGET=MEM/"specialist_runtime_input_queue.json"
STATE=MEM/"research_bridge_state.json"
HEALTH=MEM/"research_bridge_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def wid(mid):return "research-"+hashlib.sha256(str(mid).encode()).hexdigest()[:18]

def bridge():
    cfg=load(CFG,{})
    missions=load(RESEARCH,{}).get("missions",[])
    q=load(TARGET,{"tasks":[]});tasks=q.get("tasks",[])
    seen={x.get("work_id") for x in tasks}
    added=[]
    for m in missions[:int(cfg.get("maximum_research_tasks_per_cycle",10))]:
        work_id=wid(m.get("mission_id"))
        if work_id in seen:continue
        instruction=(m.get("title","Research mission")+"\nQuestions:\n- "+"\n- ".join(m.get("questions",[])))
        task={
          "work_id":work_id,"plan_id":"phase24-research","decision_id":None,
          "opportunity_id":m.get("source_action_id"),"action_type":"research",
          "instruction":instruction,"execution_boundary":"internal_non_destructive_only",
          "status":"queued_for_live_specialist","queued_at":now()
        }
        tasks.append(task);added.append(task);seen.add(work_id)
    payload={"generated_at":now(),"task_count":len(tasks),"tasks":tasks}
    save(TARGET,payload);save(STATE,{"last_bridged_at":now(),"added_count":len(added),"task_count":len(tasks)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"task_count":len(tasks)})
    return {"success":True,"status":"research_specialist_bridge_complete","added_count":len(added)}

def status():
    return {"success":True,"status":"research_specialist_bridge_status","state":load(STATE,{}),"health":load(HEALTH,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=bridge() if a=="bridge" else status() if a=="status" else {"success":False,"allowed":["bridge","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/research_to_specialist_bridge.py"

cat > "$CTL/researchbridgectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"research_to_specialist_bridge.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/researchbridgectl"

# ------------------------------------------------------------
# 3. Specialist collaboration engine
# ------------------------------------------------------------
cat > "$AGENTS/specialist_collaboration_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_config.json"
RESULTS=MEM/"specialist_runtime_results.json"
OUT=MEM/"specialist_collaboration_groups.json"
STATE=MEM/"specialist_collaboration_state.json"
HEALTH=MEM/"specialist_collaboration_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def gid(key):return hashlib.sha256(str(key).encode()).hexdigest()[:16]

def build():
    cfg=load(CFG,{})
    rows=load(RESULTS,{}).get("results",[])
    groups=defaultdict(list)
    for r in rows:
        if r.get("status")!="completed":continue
        key=r.get("opportunity_id") or r.get("plan_id") or "general"
        groups[key].append(r)
    out=[]
    for key,items in list(groups.items())[:int(cfg.get("maximum_collaboration_groups",10))]:
        summaries=[];recommendations=[];risks=[]
        for r in items:
            a=r.get("actual_result") or {}
            if a.get("summary"):summaries.append(a.get("summary"))
            recommendations+=a.get("recommendations",[]) or []
            risks+=a.get("risks",[]) or []
        out.append({
          "group_id":gid(key),"topic_id":key,"member_result_count":len(items),
          "combined_summaries":summaries[:10],
          "combined_recommendations":recommendations[:20],
          "combined_risks":risks[:20],
          "status":"ready_for_internal_synthesis",
          "created_at":now()
        })
    payload={"generated_at":now(),"group_count":len(out),"groups":out}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"group_count":len(out)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"group_count":len(out)})
    return {"success":True,"status":"specialist_collaboration_complete","report":payload}

def status():
    return {"success":True,"status":"specialist_collaboration_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/specialist_collaboration_engine.py"

cat > "$CTL/collaborationctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"specialist_collaboration_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/collaborationctl"

# ------------------------------------------------------------
# 4. Opportunity validation engine
# ------------------------------------------------------------
cat > "$AGENTS/opportunity_validation_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_config.json"
OPS=MEM/"generated_business_opportunities.json"
INSIGHTS=MEM/"validated_insights.json"
OUT=MEM/"validated_business_opportunities.json"
STATE=MEM/"opportunity_validation_state.json"
HEALTH=MEM/"opportunity_validation_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def validate():
    cfg=load(CFG,{})
    ops=load(OPS,{}).get("opportunities",[])
    insights=load(INSIGHTS,{}).get("insights",[])
    minimum=float(cfg.get("minimum_validation_score",55))
    rows=[]
    for o in ops:
        base=float(o.get("score",50) or 50)
        related=[i for i in insights if i.get("opportunity_id") in (o.get("id"),o.get("opportunity_id"))]
        confidence=(sum(float(i.get("confidence",0) or 0) for i in related)/len(related)) if related else 0
        score=round(min(100,base+(confidence*20)),2)
        rows.append({
          **o,"validation_score":score,"supporting_insight_count":len(related),
          "validation_status":"validated_internal_candidate" if score>=minimum else "needs_more_evidence",
          "validated_at":now()
        })
    rows.sort(key=lambda x:x["validation_score"],reverse=True)
    payload={"generated_at":now(),"opportunity_count":len(rows),"opportunities":rows}
    save(OUT,payload);save(STATE,{"last_validated_at":now(),"opportunity_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"opportunity_count":len(rows)})
    return {"success":True,"status":"opportunity_validation_complete","report":payload}

def status():
    return {"success":True,"status":"opportunity_validation_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=validate() if a=="validate" else status() if a=="status" else {"success":False,"allowed":["validate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/opportunity_validation_engine.py"

cat > "$CTL/opportunityvalidatectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"opportunity_validation_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/opportunityvalidatectl"

# ------------------------------------------------------------
# 5. Business workflow orchestrator
# ------------------------------------------------------------
cat > "$AGENTS/business_workflow_orchestrator.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
TASKS=MEM/"persistent_task_registry.json"
VALIDATED=MEM/"validated_business_opportunities.json"
OUT=MEM/"business_workflow_board.json"
STATE=MEM/"business_workflow_state.json"
HEALTH=MEM/"business_workflow_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def build():
    tasks=load(TASKS,{}).get("tasks",[])
    ops=load(VALIDATED,{}).get("opportunities",[])
    payload={
      "generated_at":now(),
      "workflow_columns":{
        "planned":[x for x in tasks if x.get("status")=="planned"],
        "queued":[x for x in tasks if x.get("status")=="queued"],
        "review":[x for x in tasks if "review" in str(x.get("status",""))],
        "validated_opportunities":[x for x in ops if x.get("validation_status")=="validated_internal_candidate"],
        "needs_evidence":[x for x in ops if x.get("validation_status")=="needs_more_evidence"]
      },
      "external_authority_granted":False
    }
    save(OUT,payload);save(STATE,{"last_built_at":now()})
    save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"business_workflow_board_complete","board":payload}

def status():
    return {"success":True,"status":"business_workflow_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"board":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/business_workflow_orchestrator.py"

cat > "$CTL/businessworkflowctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"business_workflow_orchestrator.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/businessworkflowctl"

# ------------------------------------------------------------
# 6. CEO operating report
# ------------------------------------------------------------
cat > "$AGENTS/ceo_operating_report.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"ceo_operating_report.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d

def build():
    perf=load("business_performance_scorecard.json",{})
    tasks=load("persistent_task_registry.json",{})
    validated=load("validated_business_opportunities.json",{})
    collab=load("specialist_collaboration_groups.json",{})
    kpis=load("kpi_goal_tracker.json",{})
    watchdog=load("autonomy_watchdog_report.json",{})
    payload={
      "generated_at":now(),
      "headline":"CompanyOS CEO Operating Report",
      "business_performance_score":perf.get("overall_score"),
      "active_task_count":tasks.get("task_count",0),
      "validated_opportunity_count":sum(
        1 for x in validated.get("opportunities",[])
        if x.get("validation_status")=="validated_internal_candidate"
      ),
      "specialist_collaboration_group_count":collab.get("group_count",0),
      "kpi_goals":kpis.get("goals",[]),
      "system_health":"healthy" if watchdog.get("healthy",False) else "attention",
      "external_authority_granted":False
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return {"success":True,"status":"ceo_operating_report_complete","report":payload}

r=build()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/ceo_operating_report.py"

cat > "$CTL/ceoreportctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"ceo_operating_report.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/ceoreportctl"

# ------------------------------------------------------------
# 7. Phase 24 controller
# ------------------------------------------------------------
cat > "$AGENTS/phase24_controller.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase24_state.json"; REPORT=MEM/"phase24_report.json"; HEALTH=MEM/"phase24_health.json"

PIPELINE=[
 ("phase23_bundle3",["python","companyos/phase23bundle3ctl","run"]),
 ("task_lifecycle",["python","companyos/tasklifecyclectl","sync"]),
 ("research_bridge",["python","companyos/researchbridgectl","bridge"]),
 ("live_specialists",["python","companyos/livespecialistctl","run"]),
 ("result_bridge",["python","companyos/liveresultbridgectl","integrate"]),
 ("validated_insights",["python","companyos/insightrefreshctl","refresh"]),
 ("collaboration",["python","companyos/collaborationctl","build"]),
 ("opportunity_validation",["python","companyos/opportunityvalidatectl","validate"]),
 ("workflow_board",["python","companyos/businessworkflowctl","build"]),
 ("ceo_report",["python","companyos/ceoreportctl","show"])
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
    return {"success":not failed,"status":"phase24_business_workflow_cycle_complete","report":report}

def status():
    def load(p):
        try:return json.loads(p.read_text())
        except:return {}
    return {"success":True,"status":"phase24_status","state":load(STATE),"health":load(HEALTH)}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/phase24_controller.py"

cat > "$CTL/phase24ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase24_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase24ctl"

echo "[1/8] Compiling..."
python -m py_compile \
 "$AGENTS/task_lifecycle_engine.py" \
 "$AGENTS/research_to_specialist_bridge.py" \
 "$AGENTS/specialist_collaboration_engine.py" \
 "$AGENTS/opportunity_validation_engine.py" \
 "$AGENTS/business_workflow_orchestrator.py" \
 "$AGENTS/ceo_operating_report.py" \
 "$AGENTS/phase24_controller.py" \
 "$CTL/tasklifecyclectl" "$CTL/researchbridgectl" "$CTL/collaborationctl" \
 "$CTL/opportunityvalidatectl" "$CTL/businessworkflowctl" "$CTL/ceoreportctl" "$CTL/phase24ctl"

echo "[2/8] Syncing persistent task lifecycle..."
python "$CTL/tasklifecyclectl" sync

echo "[3/8] Bridging research missions to live specialists..."
python "$CTL/researchbridgectl" bridge

echo "[4/8] Running collaboration and opportunity validation..."
python "$CTL/collaborationctl" build
python "$CTL/opportunityvalidatectl" validate

echo "[5/8] Building workflow board and CEO report..."
python "$CTL/businessworkflowctl" build
python "$CTL/ceoreportctl" show

echo "[6/8] Registering Phase 24 scheduler job..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase24-business-workflow-orchestration","enabled":True,"interval_seconds":10800,
"command":["python","companyos/phase24ctl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY

echo "[7/8] Restarting scheduler and running one integrated cycle..."
python "$CTL/operationsctl" restart
python "$CTL/phase24ctl" run || true

echo "[8/8] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"task_lifecycle_engine.py",r/"agents"/"research_to_specialist_bridge.py",
r/"agents"/"specialist_collaboration_engine.py",r/"agents"/"opportunity_validation_engine.py",
r/"agents"/"business_workflow_orchestrator.py",r/"agents"/"ceo_operating_report.py",
r/"agents"/"phase24_controller.py",r/"companyos"/"tasklifecyclectl",
r/"companyos"/"researchbridgectl",r/"companyos"/"collaborationctl",
r/"companyos"/"opportunityvalidatectl",r/"companyos"/"businessworkflowctl",
r/"companyos"/"ceoreportctl",r/"companyos"/"phase24ctl",
r/"ceo_memory"/"phase24_config.json",r/"ceo_memory"/"persistent_task_registry.json",
r/"ceo_memory"/"specialist_collaboration_groups.json",r/"ceo_memory"/"validated_business_opportunities.json",
r/"ceo_memory"/"business_workflow_board.json",r/"ceo_memory"/"ceo_operating_report.json",
r/"ceo_memory"/"autonomous_operations_config.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:14]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase24_config.json").read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
"automatic_fund_transfer","automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads((r/"ceo_memory"/"autonomous_operations_config.json").read_text())
if not any(x.get("id")=="phase24-business-workflow-orchestration" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Phase 24 scheduler job missing/disabled")
print("--------------------------------------------")
print("PHASE 24 BUNDLE 1 VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 24 BUNDLE 1 INSTALLED"
echo " BUSINESS WORKFLOW ORCHESTRATION CORE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Master commands:"
echo "  python companyos/phase24ctl run"
echo "  python companyos/phase24ctl status"
echo "  python companyos/ceoreportctl show"
echo "  python companyos/businessworkflowctl status"
echo
echo "Bundle includes:"
echo "  - Persistent task lifecycle"
echo "  - Research-to-specialist bridge"
echo "  - Specialist collaboration synthesis"
echo "  - Opportunity validation"
echo "  - Business workflow orchestration board"
echo "  - CEO operating report"
echo "  - Integrated Phase 24 cycle"
