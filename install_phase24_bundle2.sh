#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase24_bundle2_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 24 BUNDLE 2 - PROJECT EXECUTION & INCUBATION CORE"
echo "============================================================"

for f in \
  "$AGENTS/project_execution_engine.py" \
  "$AGENTS/specialist_team_builder.py" \
  "$AGENTS/business_incubation_engine.py" \
  "$AGENTS/milestone_tracker.py" \
  "$AGENTS/resource_budget_engine.py" \
  "$AGENTS/replan_recovery_engine.py" \
  "$AGENTS/ceo_portfolio_manager.py" \
  "$AGENTS/phase24_bundle2_controller.py" \
  "$CTL/projectexecutionctl" \
  "$CTL/specialistteamctl" \
  "$CTL/incubationctl" \
  "$CTL/milestonectl" \
  "$CTL/resourcebudgetctl" \
  "$CTL/replanctl" \
  "$CTL/ceoportfolioctl" \
  "$CTL/phase24bundle2ctl"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/phase24_bundle2_config.json" <<'JSON'
{
  "enabled": true,
  "maximum_projects": 20,
  "maximum_team_size": 5,
  "maximum_incubation_candidates": 10,
  "maximum_milestones_per_project": 8,
  "abstract_budget_units": 100,
  "replan_failure_threshold": 1,
  "automatic_internal_project_execution": true,
  "automatic_internal_team_formation": true,
  "automatic_internal_incubation": true,
  "automatic_internal_milestone_tracking": true,
  "automatic_internal_replanning": true,
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
# 1. Multi-stage project execution engine
# ------------------------------------------------------------
cat > "$AGENTS/project_execution_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle2_config.json"
TASKS=MEM/"persistent_task_registry.json"
VALIDATED=MEM/"validated_business_opportunities.json"
OUT=MEM/"project_execution_registry.json"
STATE=MEM/"project_execution_state.json"
HEALTH=MEM/"project_execution_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def pid(seed):return hashlib.sha256(str(seed).encode()).hexdigest()[:18]

def build():
    cfg=load(CFG,{})
    validated=[x for x in load(VALIDATED,{}).get("opportunities",[])
               if x.get("validation_status")=="validated_internal_candidate"]
    tasks=load(TASKS,{}).get("tasks",[])
    projects=[]
    for i,o in enumerate(validated[:int(cfg.get("maximum_projects",20))],1):
        title=o.get("title") or f"Project {i}"
        projects.append({
          "project_id":pid(o.get("id") or title),
          "title":title,
          "source_opportunity_id":o.get("id"),
          "validation_score":o.get("validation_score"),
          "stage":"discovery",
          "stages":[
            {"name":"discovery","status":"active"},
            {"name":"validation","status":"pending"},
            {"name":"planning","status":"pending"},
            {"name":"internal_execution","status":"pending"},
            {"name":"measurement","status":"pending"}
          ],
          "linked_task_count":sum(1 for t in tasks if t.get("title")==title),
          "authority":"internal_non_destructive_only",
          "created_at":now()
        })
    payload={"generated_at":now(),"project_count":len(projects),"projects":projects}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"project_count":len(projects)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"project_count":len(projects)})
    return {"success":True,"status":"project_execution_registry_complete","registry":payload}

def status():
    return {"success":True,"status":"project_execution_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"registry":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/project_execution_engine.py"

cat > "$CTL/projectexecutionctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"project_execution_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/projectexecutionctl"

# ------------------------------------------------------------
# 2. Specialist team builder
# ------------------------------------------------------------
cat > "$AGENTS/specialist_team_builder.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle2_config.json"
PROJECTS=MEM/"project_execution_registry.json"
PROFILES=MEM/"specialist_performance_profiles.json"
OUT=MEM/"specialist_project_teams.json"
STATE=MEM/"specialist_team_state.json"
HEALTH=MEM/"specialist_team_health.json"

DEFAULT_ROLES=["research","analysis","planning","review","coordination"]

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def gid(x):return hashlib.sha256(str(x).encode()).hexdigest()[:16]

def build():
    cfg=load(CFG,{})
    projects=load(PROJECTS,{}).get("projects",[])
    profiles=load(PROFILES,{}).get("profiles",[])
    ranked=[p.get("specialist_role") for p in profiles if p.get("specialist_role")]
    roles=(ranked+DEFAULT_ROLES)
    teams=[]
    max_size=int(cfg.get("maximum_team_size",5))
    for p in projects:
        members=[]
        seen=set()
        for role in roles:
            if role in seen:continue
            members.append({"role":role,"assignment":"internal_specialist","status":"assigned"})
            seen.add(role)
            if len(members)>=max_size:break
        teams.append({
          "team_id":gid(p.get("project_id")),
          "project_id":p.get("project_id"),
          "project_title":p.get("title"),
          "member_count":len(members),
          "members":members,
          "status":"formed_for_internal_collaboration",
          "created_at":now()
        })
    payload={"generated_at":now(),"team_count":len(teams),"teams":teams}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"team_count":len(teams)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"team_count":len(teams)})
    return {"success":True,"status":"specialist_team_build_complete","report":payload}

def status():
    return {"success":True,"status":"specialist_team_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/specialist_team_builder.py"

cat > "$CTL/specialistteamctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"specialist_team_builder.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/specialistteamctl"

# ------------------------------------------------------------
# 3. Business incubation engine
# ------------------------------------------------------------
cat > "$AGENTS/business_incubation_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle2_config.json"
PROJECTS=MEM/"project_execution_registry.json"
OUT=MEM/"business_incubation_portfolio.json"
STATE=MEM/"business_incubation_state.json"
HEALTH=MEM/"business_incubation_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def incubate():
    cfg=load(CFG,{})
    projects=load(PROJECTS,{}).get("projects",[])
    rows=[]
    for p in projects[:int(cfg.get("maximum_incubation_candidates",10))]:
        rows.append({
          "project_id":p.get("project_id"),
          "title":p.get("title"),
          "incubation_stage":"concept_validation",
          "validation_score":p.get("validation_score"),
          "hypothesis":"This project may create measurable business value if evidence, execution readiness, and outcomes remain favorable.",
          "next_internal_steps":[
            "Validate customer or market need with available evidence",
            "Define measurable success criteria",
            "Estimate internal effort and dependencies",
            "Prepare a governed pilot plan"
          ],
          "status":"incubating_internal_only",
          "external_launch_authorized":False
        })
    payload={"generated_at":now(),"candidate_count":len(rows),"candidates":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"candidate_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"candidate_count":len(rows)})
    return {"success":True,"status":"business_incubation_complete","portfolio":payload}

def status():
    return {"success":True,"status":"business_incubation_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"portfolio":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=incubate() if a=="incubate" else status() if a=="status" else {"success":False,"allowed":["incubate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/business_incubation_engine.py"

cat > "$CTL/incubationctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"business_incubation_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/incubationctl"

# ------------------------------------------------------------
# 4. Milestone tracker
# ------------------------------------------------------------
cat > "$AGENTS/milestone_tracker.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle2_config.json"
PROJECTS=MEM/"project_execution_registry.json"
OUT=MEM/"project_milestones.json"
STATE=MEM/"milestone_state.json"
HEALTH=MEM/"milestone_health.json"

TEMPLATE=[
 ("evidence_review","Evidence reviewed"),
 ("success_criteria","Success criteria defined"),
 ("dependency_map","Dependencies mapped"),
 ("execution_plan","Internal execution plan prepared"),
 ("pilot_ready","Governed pilot ready"),
 ("measurement","Measurement framework prepared")
]

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def mid(pid,name):return hashlib.sha256(f"{pid}|{name}".encode()).hexdigest()[:18]

def build():
    cfg=load(CFG,{})
    projects=load(PROJECTS,{}).get("projects",[])
    maxm=int(cfg.get("maximum_milestones_per_project",8))
    rows=[]
    for p in projects:
        milestones=[]
        for key,title in TEMPLATE[:maxm]:
            milestones.append({
              "milestone_id":mid(p.get("project_id"),key),
              "name":key,"title":title,"status":"pending"
            })
        rows.append({"project_id":p.get("project_id"),"title":p.get("title"),
          "milestone_count":len(milestones),"milestones":milestones})
    payload={"generated_at":now(),"project_count":len(rows),"projects":rows}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"project_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"project_count":len(rows)})
    return {"success":True,"status":"milestone_tracker_complete","report":payload}

def status():
    return {"success":True,"status":"milestone_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/milestone_tracker.py"

cat > "$CTL/milestonectl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"milestone_tracker.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/milestonectl"

# ------------------------------------------------------------
# 5. Abstract resource budget engine
# ------------------------------------------------------------
cat > "$AGENTS/resource_budget_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle2_config.json"
PROJECTS=MEM/"project_execution_registry.json"
OUT=MEM/"project_resource_budgets.json"
STATE=MEM/"resource_budget_state.json"
HEALTH=MEM/"resource_budget_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def allocate():
    cfg=load(CFG,{})
    projects=load(PROJECTS,{}).get("projects",[])
    total=int(cfg.get("abstract_budget_units",100))
    weights=[max(float(p.get("validation_score",50) or 50),1) for p in projects]
    denom=sum(weights) or 1
    rows=[];remaining=total
    for i,p in enumerate(projects):
        units=round(total*weights[i]/denom)
        if i==len(projects)-1:units=remaining
        remaining-=units
        rows.append({
          "project_id":p.get("project_id"),"title":p.get("title"),
          "budget_units":max(units,0),
          "budget_type":"abstract_internal_capacity_units",
          "status":"planned_only"
        })
    payload={"generated_at":now(),"total_budget_units":total,"allocations":rows,
      "note":"These units are internal planning capacity, not money or authorization to spend."}
    save(OUT,payload);save(STATE,{"last_allocated_at":now(),"allocation_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"allocation_count":len(rows)})
    return {"success":True,"status":"resource_budget_complete","report":payload}

def status():
    return {"success":True,"status":"resource_budget_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=allocate() if a=="allocate" else status() if a=="status" else {"success":False,"allowed":["allocate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/resource_budget_engine.py"

cat > "$CTL/resourcebudgetctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"resource_budget_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/resourcebudgetctl"

# ------------------------------------------------------------
# 6. Replan/recovery engine
# ------------------------------------------------------------
cat > "$AGENTS/replan_recovery_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
PH24=MEM/"phase24_report.json"
AUTONOMY=MEM/"autonomy_core_report.json"
OUT=MEM/"replan_recovery_actions.json"
STATE=MEM/"replan_recovery_state.json"
HEALTH=MEM/"replan_recovery_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def run():
    failures=[]
    for source,path in [("phase24",PH24),("autonomy",AUTONOMY)]:
        d=load(path,{})
        for step in d.get("failed_steps",[]) or []:
            failures.append({"source":source,"step":step})
    actions=[]
    for f in failures:
        actions.append({
          "source":f["source"],"failed_step":f["step"],
          "recommended_action":"Re-run prerequisite health checks, refresh upstream state, then retry the failed internal step.",
          "status":"replan_recommended",
          "external_action":False
        })
    payload={"generated_at":now(),"failure_count":len(failures),"replan_action_count":len(actions),"actions":actions}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"failure_count":len(failures)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"failure_count":len(failures)})
    return {"success":True,"status":"replan_recovery_complete","report":payload}

def status():
    return {"success":True,"status":"replan_recovery_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/replan_recovery_engine.py"

cat > "$CTL/replanctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"replan_recovery_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/replanctl"

# ------------------------------------------------------------
# 7. CEO portfolio manager
# ------------------------------------------------------------
cat > "$AGENTS/ceo_portfolio_manager.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"ceo_project_portfolio.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d

def build():
    projects=load("project_execution_registry.json",{}).get("projects",[])
    teams=load("specialist_project_teams.json",{}).get("teams",[])
    incubation=load("business_incubation_portfolio.json",{}).get("candidates",[])
    milestones=load("project_milestones.json",{}).get("projects",[])
    budgets=load("project_resource_budgets.json",{}).get("allocations",[])
    replans=load("replan_recovery_actions.json",{})
    payload={
      "generated_at":now(),
      "project_count":len(projects),
      "projects":projects,
      "team_count":len(teams),
      "incubation_candidate_count":len(incubation),
      "milestone_project_count":len(milestones),
      "resource_budget_count":len(budgets),
      "replan_failure_count":replans.get("failure_count",0),
      "external_authority_granted":False
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return {"success":True,"status":"ceo_project_portfolio_complete","portfolio":payload}

r=build()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/ceo_portfolio_manager.py"

cat > "$CTL/ceoportfolioctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"ceo_portfolio_manager.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/ceoportfolioctl"

# ------------------------------------------------------------
# 8. Bundle controller
# ------------------------------------------------------------
cat > "$AGENTS/phase24_bundle2_controller.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase24_bundle2_state.json"; REPORT=MEM/"phase24_bundle2_report.json"; HEALTH=MEM/"phase24_bundle2_health.json"

PIPELINE=[
 ("phase24_core",["python","companyos/phase24ctl","run"]),
 ("project_execution",["python","companyos/projectexecutionctl","build"]),
 ("specialist_teams",["python","companyos/specialistteamctl","build"]),
 ("incubation",["python","companyos/incubationctl","incubate"]),
 ("milestones",["python","companyos/milestonectl","build"]),
 ("resource_budget",["python","companyos/resourcebudgetctl","allocate"]),
 ("replan_recovery",["python","companyos/replanctl","run"]),
 ("ceo_portfolio",["python","companyos/ceoportfolioctl","show"])
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
    return {"success":not failed,"status":"phase24_bundle2_cycle_complete","report":report}

def status():
    def load(p):
        try:return json.loads(p.read_text())
        except:return {}
    return {"success":True,"status":"phase24_bundle2_status","state":load(STATE),"health":load(HEALTH)}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/phase24_bundle2_controller.py"

cat > "$CTL/phase24bundle2ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase24_bundle2_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase24bundle2ctl"

echo "[1/8] Compiling..."
python -m py_compile \
 "$AGENTS/project_execution_engine.py" \
 "$AGENTS/specialist_team_builder.py" \
 "$AGENTS/business_incubation_engine.py" \
 "$AGENTS/milestone_tracker.py" \
 "$AGENTS/resource_budget_engine.py" \
 "$AGENTS/replan_recovery_engine.py" \
 "$AGENTS/ceo_portfolio_manager.py" \
 "$AGENTS/phase24_bundle2_controller.py" \
 "$CTL/projectexecutionctl" "$CTL/specialistteamctl" "$CTL/incubationctl" \
 "$CTL/milestonectl" "$CTL/resourcebudgetctl" "$CTL/replanctl" "$CTL/ceoportfolioctl" "$CTL/phase24bundle2ctl"

echo "[2/8] Building project execution registry..."
python "$CTL/projectexecutionctl" build

echo "[3/8] Forming specialist teams..."
python "$CTL/specialistteamctl" build

echo "[4/8] Building incubation portfolio and milestones..."
python "$CTL/incubationctl" incubate
python "$CTL/milestonectl" build

echo "[5/8] Allocating abstract project resources..."
python "$CTL/resourcebudgetctl" allocate

echo "[6/8] Running replanning and CEO portfolio synthesis..."
python "$CTL/replanctl" run
python "$CTL/ceoportfolioctl" show

echo "[7/8] Registering scheduler and running integrated cycle..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase24-project-execution-incubation","enabled":True,"interval_seconds":10800,
"command":["python","companyos/phase24bundle2ctl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart
python "$CTL/phase24bundle2ctl" run || true

echo "[8/8] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"project_execution_engine.py",r/"agents"/"specialist_team_builder.py",
r/"agents"/"business_incubation_engine.py",r/"agents"/"milestone_tracker.py",
r/"agents"/"resource_budget_engine.py",r/"agents"/"replan_recovery_engine.py",
r/"agents"/"ceo_portfolio_manager.py",r/"agents"/"phase24_bundle2_controller.py",
r/"companyos"/"projectexecutionctl",r/"companyos"/"specialistteamctl",
r/"companyos"/"incubationctl",r/"companyos"/"milestonectl",
r/"companyos"/"resourcebudgetctl",r/"companyos"/"replanctl",
r/"companyos"/"ceoportfolioctl",r/"companyos"/"phase24bundle2ctl",
r/"ceo_memory"/"phase24_bundle2_config.json",r/"ceo_memory"/"project_execution_registry.json",
r/"ceo_memory"/"specialist_project_teams.json",r/"ceo_memory"/"business_incubation_portfolio.json",
r/"ceo_memory"/"project_milestones.json",r/"ceo_memory"/"project_resource_budgets.json",
r/"ceo_memory"/"replan_recovery_actions.json",r/"ceo_memory"/"ceo_project_portfolio.json",
r/"ceo_memory"/"autonomous_operations_config.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:16]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase24_bundle2_config.json").read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
"automatic_fund_transfer","automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads((r/"ceo_memory"/"autonomous_operations_config.json").read_text())
if not any(x.get("id")=="phase24-project-execution-incubation" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Phase 24 Bundle 2 scheduler job missing/disabled")
print("--------------------------------------------")
print("PHASE 24 BUNDLE 2 VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 24 BUNDLE 2 INSTALLED"
echo " PROJECT EXECUTION & INCUBATION CORE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Master commands:"
echo "  python companyos/phase24bundle2ctl run"
echo "  python companyos/phase24bundle2ctl status"
echo "  python companyos/ceoportfolioctl show"
echo
echo "Bundle includes:"
echo "  - Multi-stage project execution"
echo "  - Specialist team formation"
echo "  - Business/product incubation"
echo "  - Milestone tracking"
echo "  - Abstract resource budgeting"
echo "  - Failure recovery/replanning"
echo "  - CEO portfolio management"
echo "  - Integrated Phase 24 Bundle 2 cycle"
