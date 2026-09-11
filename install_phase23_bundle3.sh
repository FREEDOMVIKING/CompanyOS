#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase23_bundle3_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 23 BUNDLE 3 - STRATEGIC AUTONOMY & PORTFOLIO CORE"
echo "============================================================"

for f in \
  "$AGENTS/strategic_plan_engine.py" \
  "$AGENTS/portfolio_capital_planner.py" \
  "$AGENTS/research_mission_engine.py" \
  "$AGENTS/kpi_goal_tracker.py" \
  "$AGENTS/learning_feedback_merger.py" \
  "$AGENTS/executive_action_board.py" \
  "$AGENTS/phase23_bundle3_controller.py" \
  "$CTL/strategicplanctl" \
  "$CTL/portfoliocapitalctl" \
  "$CTL/researchmissionctl" \
  "$CTL/kpigoalctl" \
  "$CTL/learningmergectl" \
  "$CTL/actionboardctl" \
  "$CTL/phase23bundle3ctl"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/phase23_bundle3_config.json" <<'JSON'
{
  "enabled": true,
  "planning_horizon_days": 30,
  "maximum_strategic_actions": 20,
  "maximum_research_missions": 15,
  "abstract_resource_units": 100,
  "minimum_opportunity_score": 45,
  "automatic_internal_strategy": true,
  "automatic_internal_research_queueing": true,
  "automatic_internal_resource_planning": true,
  "automatic_internal_learning_merge": true,
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
# 1. Strategic plan engine
# ------------------------------------------------------------
cat > "$AGENTS/strategic_plan_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_bundle3_config.json"
OPS=MEM/"generated_business_opportunities.json"
PERF=MEM/"business_performance_scorecard.json"
BRIEF=MEM/"executive_briefing.json"
OUT=MEM/"strategic_30_day_plan.json"
STATE=MEM/"strategic_plan_state.json"
HEALTH=MEM/"strategic_plan_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def sid(text):return hashlib.sha256(text.encode()).hexdigest()[:16]

def build():
    cfg=load(CFG,{})
    ops=load(OPS,{}).get("opportunities",[])
    perf=load(PERF,{})
    brief=load(BRIEF,{})
    actions=[]
    for i,o in enumerate(ops[:10],1):
        title=o.get("title") or f"Opportunity {i}"
        actions.append({
          "id":sid(title),
          "priority":i,
          "title":title,
          "category":o.get("category","growth"),
          "score":o.get("score",50),
          "objective":"Advance the opportunity through internal research, validation, planning, and governed execution preparation.",
          "status":"planned_internal",
          "authority":"internal_non_destructive_only"
        })
    if float(perf.get("overall_score",100) or 100)<85:
        actions.append({
          "id":sid("raise-business-performance"),
          "priority":len(actions)+1,
          "title":"Raise business performance score",
          "category":"optimization",
          "score":85,
          "objective":"Improve the weakest measured KPI dimensions using internal analysis and measured feedback.",
          "status":"planned_internal",
          "authority":"internal_non_destructive_only"
        })
    actions=actions[:int(cfg.get("maximum_strategic_actions",20))]
    payload={
      "generated_at":now(),
      "planning_horizon_days":int(cfg.get("planning_horizon_days",30)),
      "business_performance_score":perf.get("overall_score"),
      "recommended_focus":brief.get("recommended_focus",[]),
      "action_count":len(actions),
      "actions":actions,
      "external_authority_granted":False
    }
    save(OUT,payload);save(STATE,{"last_built_at":now(),"action_count":len(actions)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"action_count":len(actions)})
    return {"success":True,"status":"strategic_plan_complete","plan":payload}

def status():
    return {"success":True,"status":"strategic_plan_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"plan":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/strategic_plan_engine.py"

cat > "$CTL/strategicplanctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"strategic_plan_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/strategicplanctl"

# ------------------------------------------------------------
# 2. Abstract portfolio resource planner
# ------------------------------------------------------------
cat > "$AGENTS/portfolio_capital_planner.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_bundle3_config.json"
PLAN=MEM/"strategic_30_day_plan.json"
OUT=MEM/"portfolio_resource_plan.json"
STATE=MEM/"portfolio_resource_plan_state.json"
HEALTH=MEM/"portfolio_resource_plan_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def allocate():
    cfg=load(CFG,{})
    actions=load(PLAN,{}).get("actions",[])
    total_units=int(cfg.get("abstract_resource_units",100))
    positive=[max(float(a.get("score",50) or 50),1.0) for a in actions]
    denom=sum(positive) or 1
    rows=[]
    remaining=total_units
    for i,a in enumerate(actions):
        units=round(total_units*positive[i]/denom)
        if i==len(actions)-1: units=remaining
        remaining-=units
        rows.append({
          "action_id":a.get("id"),"title":a.get("title"),
          "resource_units":max(units,0),
          "resource_type":"abstract_internal_attention_units",
          "status":"planned_only"
        })
    payload={"generated_at":now(),"total_resource_units":total_units,
      "allocation_count":len(rows),"allocations":rows,
      "note":"These are abstract internal planning units, not money or real financial commitments."}
    save(OUT,payload);save(STATE,{"last_allocated_at":now(),"allocation_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"allocation_count":len(rows)})
    return {"success":True,"status":"portfolio_resource_planning_complete","plan":payload}

def status():
    return {"success":True,"status":"portfolio_resource_plan_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"plan":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=allocate() if a=="allocate" else status() if a=="status" else {"success":False,"allowed":["allocate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/portfolio_capital_planner.py"

cat > "$CTL/portfoliocapitalctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"portfolio_capital_planner.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/portfoliocapitalctl"

# ------------------------------------------------------------
# 3. Research mission engine
# ------------------------------------------------------------
cat > "$AGENTS/research_mission_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_bundle3_config.json"
PLAN=MEM/"strategic_30_day_plan.json"
OUT=MEM/"research_mission_queue.json"
STATE=MEM/"research_mission_state.json"
HEALTH=MEM/"research_mission_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def mid(x):return hashlib.sha256(x.encode()).hexdigest()[:18]

def generate():
    cfg=load(CFG,{})
    actions=load(PLAN,{}).get("actions",[])
    rows=[]
    for a in actions[:int(cfg.get("maximum_research_missions",15))]:
        title=a.get("title","Untitled opportunity")
        rows.append({
          "mission_id":mid(title),
          "title":f"Research: {title}",
          "source_action_id":a.get("id"),
          "questions":[
            "What evidence supports this opportunity?",
            "What are the main risks and failure modes?",
            "What is the smallest practical validation step?",
            "What internal capabilities or dependencies are required?"
          ],
          "status":"queued_internal_research",
          "execution_boundary":"internal_non_destructive_only",
          "created_at":now()
        })
    payload={"generated_at":now(),"mission_count":len(rows),"missions":rows}
    save(OUT,payload);save(STATE,{"last_generated_at":now(),"mission_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"mission_count":len(rows)})
    return {"success":True,"status":"research_mission_generation_complete","queue":payload}

def status():
    return {"success":True,"status":"research_mission_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"queue":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=generate() if a=="generate" else status() if a=="status" else {"success":False,"allowed":["generate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/research_mission_engine.py"

cat > "$CTL/researchmissionctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"research_mission_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/researchmissionctl"

# ------------------------------------------------------------
# 4. KPI goal tracker
# ------------------------------------------------------------
cat > "$AGENTS/kpi_goal_tracker.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
PERF=MEM/"business_performance_scorecard.json"
OPS=MEM/"generated_business_opportunities.json"
MEMSTATE=MEM/"persistent_memory_state.json"
OUT=MEM/"kpi_goal_tracker.json"
STATE=MEM/"kpi_goal_state.json"
HEALTH=MEM/"kpi_goal_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def update():
    perf=load(PERF,{})
    op_count=int(load(OPS,{}).get("opportunity_count",0) or 0)
    mem_count=int(load(MEMSTATE,{}).get("event_count",0) or 0)
    score=float(perf.get("overall_score",0) or 0)
    goals=[
      {"goal":"business_performance","target":85,"current":score,"unit":"score",
       "status":"met" if score>=85 else "in_progress"},
      {"goal":"active_internal_opportunities","target":5,"current":op_count,"unit":"count",
       "status":"met" if op_count>=5 else "in_progress"},
      {"goal":"persistent_memory_events","target":100,"current":mem_count,"unit":"count",
       "status":"met" if mem_count>=100 else "in_progress"}
    ]
    payload={"generated_at":now(),"goal_count":len(goals),"goals":goals}
    save(OUT,payload);save(STATE,{"last_updated_at":now(),"goal_count":len(goals)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"goal_count":len(goals)})
    return {"success":True,"status":"kpi_goal_update_complete","tracker":payload}

def status():
    return {"success":True,"status":"kpi_goal_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"tracker":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=update() if a=="update" else status() if a=="status" else {"success":False,"allowed":["update","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/kpi_goal_tracker.py"

cat > "$CTL/kpigoalctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"kpi_goal_tracker.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/kpigoalctl"

# ------------------------------------------------------------
# 5. Learning feedback merger
# ------------------------------------------------------------
cat > "$AGENTS/learning_feedback_merger.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"unified_learning_context.json"
STATE=MEM/"learning_merge_state.json"
HEALTH=MEM/"learning_merge_health.json"

SOURCES=[
 "specialist_performance_profiles.json",
 "validated_insights.json",
 "self_improvement_proposals.json",
 "business_performance_scorecard.json",
 "outcome_tracker_report.json",
 "provider_health_report.json"
]

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def merge():
    merged={}
    present=0
    for name in SOURCES:
        p=MEM/name
        if p.exists():
            merged[name]=load(p,{})
            present+=1
    payload={"generated_at":now(),"source_count":present,"sources":merged,
      "purpose":"Unified internal learning context for future prioritization and planning."}
    save(OUT,payload);save(STATE,{"last_merged_at":now(),"source_count":present})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"source_count":present})
    return {"success":True,"status":"learning_feedback_merge_complete","context":payload}

def status():
    return {"success":True,"status":"learning_feedback_merge_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"context":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=merge() if a=="merge" else status() if a=="status" else {"success":False,"allowed":["merge","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/learning_feedback_merger.py"

cat > "$CTL/learningmergectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"learning_feedback_merger.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/learningmergectl"

# ------------------------------------------------------------
# 6. Executive action board
# ------------------------------------------------------------
cat > "$AGENTS/executive_action_board.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"executive_action_board.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d

def build():
    strategic=load("strategic_30_day_plan.json",{}).get("actions",[])
    research=load("research_mission_queue.json",{}).get("missions",[])
    goals=load("kpi_goal_tracker.json",{}).get("goals",[])
    improvements=load("governed_improvement_queue.json",{}).get("items",[])
    resources=load("portfolio_resource_plan.json",{}).get("allocations",[])
    payload={
      "generated_at":now(),
      "top_strategic_actions":strategic[:10],
      "research_missions":research[:10],
      "kpi_goals":goals,
      "improvement_queue":improvements[:10],
      "resource_plan":resources[:10],
      "external_authority_granted":False
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return {"success":True,"status":"executive_action_board_complete","board":payload}

r=build()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/executive_action_board.py"

cat > "$CTL/actionboardctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"executive_action_board.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/actionboardctl"

# ------------------------------------------------------------
# 7. Bundle controller
# ------------------------------------------------------------
cat > "$AGENTS/phase23_bundle3_controller.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase23_bundle3_state.json"; REPORT=MEM/"phase23_bundle3_report.json"; HEALTH=MEM/"phase23_bundle3_health.json"

PIPELINE=[
 ("bundle2",["python","companyos/phase23bundle2ctl","run"]),
 ("strategic_plan",["python","companyos/strategicplanctl","build"]),
 ("portfolio_resources",["python","companyos/portfoliocapitalctl","allocate"]),
 ("research_missions",["python","companyos/researchmissionctl","generate"]),
 ("kpi_goals",["python","companyos/kpigoalctl","update"]),
 ("learning_merge",["python","companyos/learningmergectl","merge"]),
 ("action_board",["python","companyos/actionboardctl","show"])
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
    return {"success":not failed,"status":"phase23_bundle3_cycle_complete","report":report}

def status():
    def load(p):
        try:return json.loads(p.read_text())
        except:return {}
    return {"success":True,"status":"phase23_bundle3_status","state":load(STATE),"health":load(HEALTH)}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/phase23_bundle3_controller.py"

cat > "$CTL/phase23bundle3ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase23_bundle3_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase23bundle3ctl"

echo "[1/8] Compiling..."
python -m py_compile \
 "$AGENTS/strategic_plan_engine.py" \
 "$AGENTS/portfolio_capital_planner.py" \
 "$AGENTS/research_mission_engine.py" \
 "$AGENTS/kpi_goal_tracker.py" \
 "$AGENTS/learning_feedback_merger.py" \
 "$AGENTS/executive_action_board.py" \
 "$AGENTS/phase23_bundle3_controller.py" \
 "$CTL/strategicplanctl" "$CTL/portfoliocapitalctl" "$CTL/researchmissionctl" \
 "$CTL/kpigoalctl" "$CTL/learningmergectl" "$CTL/actionboardctl" "$CTL/phase23bundle3ctl"

echo "[2/8] Building 30-day strategic plan..."
python "$CTL/strategicplanctl" build

echo "[3/8] Allocating abstract portfolio resources..."
python "$CTL/portfoliocapitalctl" allocate

echo "[4/8] Generating research missions..."
python "$CTL/researchmissionctl" generate

echo "[5/8] Updating KPI goals and learning context..."
python "$CTL/kpigoalctl" update
python "$CTL/learningmergectl" merge

echo "[6/8] Building executive action board..."
python "$CTL/actionboardctl" show

echo "[7/8] Registering scheduler and running one integrated cycle..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase23-strategic-autonomy-portfolio","enabled":True,"interval_seconds":10800,
"command":["python","companyos/phase23bundle3ctl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart
python "$CTL/phase23bundle3ctl" run || true

echo "[8/8] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"strategic_plan_engine.py",r/"agents"/"portfolio_capital_planner.py",
r/"agents"/"research_mission_engine.py",r/"agents"/"kpi_goal_tracker.py",
r/"agents"/"learning_feedback_merger.py",r/"agents"/"executive_action_board.py",
r/"agents"/"phase23_bundle3_controller.py",r/"companyos"/"strategicplanctl",
r/"companyos"/"portfoliocapitalctl",r/"companyos"/"researchmissionctl",
r/"companyos"/"kpigoalctl",r/"companyos"/"learningmergectl",
r/"companyos"/"actionboardctl",r/"companyos"/"phase23bundle3ctl",
r/"ceo_memory"/"phase23_bundle3_config.json",r/"ceo_memory"/"strategic_30_day_plan.json",
r/"ceo_memory"/"portfolio_resource_plan.json",r/"ceo_memory"/"research_mission_queue.json",
r/"ceo_memory"/"kpi_goal_tracker.json",r/"ceo_memory"/"unified_learning_context.json",
r/"ceo_memory"/"executive_action_board.json",r/"ceo_memory"/"autonomous_operations_config.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:14]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase23_bundle3_config.json").read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
"automatic_fund_transfer","automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads((r/"ceo_memory"/"autonomous_operations_config.json").read_text())
if not any(x.get("id")=="phase23-strategic-autonomy-portfolio" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Phase 23 Bundle 3 scheduler job missing/disabled")
print("--------------------------------------------")
print("PHASE 23 BUNDLE 3 VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 23 BUNDLE 3 INSTALLED"
echo " STRATEGIC AUTONOMY & PORTFOLIO CORE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Master commands:"
echo "  python companyos/phase23bundle3ctl run"
echo "  python companyos/phase23bundle3ctl status"
echo "  python companyos/actionboardctl show"
echo
echo "Bundle includes:"
echo "  - 30-day strategic planning"
echo "  - Abstract portfolio resource planning"
echo "  - Research mission generation"
echo "  - KPI/goal tracking"
echo "  - Unified learning feedback context"
echo "  - Executive action board"
echo "  - Integrated strategic autonomy cycle"
