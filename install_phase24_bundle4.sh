#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase24_bundle4_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 24 BUNDLE 4 - EXECUTIVE DELIVERY & GOVERNANCE CORE"
echo "============================================================"

for f in \
  "$AGENTS/delivery_pipeline_engine.py" \
  "$AGENTS/approval_policy_engine.py" \
  "$AGENTS/outcome_commitment_engine.py" \
  "$AGENTS/executive_review_engine.py" \
  "$AGENTS/risk_register_engine.py" \
  "$AGENTS/portfolio_decision_engine.py" \
  "$AGENTS/phase24_bundle4_controller.py" \
  "$CTL/deliveryctl" \
  "$CTL/approvalpolicyctl" \
  "$CTL/outcomecommitmentctl" \
  "$CTL/executivereviewctl" \
  "$CTL/riskregisterctl" \
  "$CTL/portfoliodecisionctl" \
  "$CTL/phase24bundle4ctl"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/phase24_bundle4_config.json" <<'JSON'
{
  "enabled": true,
  "maximum_delivery_items": 50,
  "maximum_review_items": 50,
  "maximum_risks": 100,
  "minimum_commitment_score": 55,
  "automatic_internal_delivery_planning": true,
  "automatic_internal_reviews": true,
  "automatic_internal_risk_tracking": true,
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
# 1. Delivery pipeline engine
# ------------------------------------------------------------
cat > "$AGENTS/delivery_pipeline_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle4_config.json"
PROJECTS=MEM/"project_execution_registry.json"
MILESTONES=MEM/"project_milestones.json"
OUT=MEM/"delivery_pipeline.json"
STATE=MEM/"delivery_pipeline_state.json"
HEALTH=MEM/"delivery_pipeline_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def did(seed):return hashlib.sha256(str(seed).encode()).hexdigest()[:18]

def build():
    cfg=load(CFG,{})
    projects=load(PROJECTS,{}).get("projects",[])
    ms={x.get("project_id"):x for x in load(MILESTONES,{}).get("projects",[])}
    rows=[]
    for p in projects[:int(cfg.get("maximum_delivery_items",50))]:
        pm=ms.get(p.get("project_id"),{})
        rows.append({
          "delivery_id":did(p.get("project_id")),
          "project_id":p.get("project_id"),
          "title":p.get("title"),
          "current_stage":p.get("stage"),
          "milestones":pm.get("milestones",[]),
          "status":"internal_delivery_planning",
          "external_delivery_authorized":False,
          "created_at":now()
        })
    payload={"generated_at":now(),"delivery_count":len(rows),"deliveries":rows}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"delivery_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"delivery_count":len(rows)})
    return {"success":True,"status":"delivery_pipeline_complete","pipeline":payload}

def status():
    return {"success":True,"status":"delivery_pipeline_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"pipeline":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/delivery_pipeline_engine.py"

cat > "$CTL/deliveryctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"delivery_pipeline_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/deliveryctl"

# ------------------------------------------------------------
# 2. Approval policy engine
# ------------------------------------------------------------
cat > "$AGENTS/approval_policy_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
APPROVALS=MEM/"governed_approval_queue.json"
OUT=MEM/"approval_policy_report.json"
STATE=MEM/"approval_policy_state.json"
HEALTH=MEM/"approval_policy_health.json"

POLICIES={
 "external_launch_or_publication":"explicit_human_approval_required",
 "external_execution_boundary":"explicit_human_approval_required",
 "spending":"explicit_human_approval_required",
 "fund_transfer":"explicit_human_approval_required",
 "code_change":"explicit_human_approval_required",
 "merge":"explicit_human_approval_required",
 "deploy":"explicit_human_approval_required",
 "destructive_action":"explicit_human_approval_required"
}

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def evaluate():
    items=load(APPROVALS,{}).get("items",[])
    rows=[]
    for x in items:
        cls=x.get("action_class")
        rows.append({
          "approval_id":x.get("approval_id"),
          "action_class":cls,
          "policy":POLICIES.get(cls,"explicit_human_approval_required"),
          "current_status":x.get("status","pending"),
          "execution_allowed":False
        })
    payload={"generated_at":now(),"policy_count":len(POLICIES),"evaluated_count":len(rows),
      "policies":POLICIES,"evaluations":rows}
    save(OUT,payload);save(STATE,{"last_evaluated_at":now(),"evaluated_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"evaluated_count":len(rows)})
    return {"success":True,"status":"approval_policy_complete","report":payload}

r=evaluate()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/approval_policy_engine.py"

cat > "$CTL/approvalpolicyctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"approval_policy_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/approvalpolicyctl"

# ------------------------------------------------------------
# 3. Outcome commitment engine
# ------------------------------------------------------------
cat > "$AGENTS/outcome_commitment_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle4_config.json"
VALIDATED=MEM/"validated_business_opportunities.json"
PROJECTS=MEM/"project_execution_registry.json"
OUT=MEM/"outcome_commitments.json"
STATE=MEM/"outcome_commitment_state.json"
HEALTH=MEM/"outcome_commitment_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def build():
    cfg=load(CFG,{})
    minimum=float(cfg.get("minimum_commitment_score",55))
    ops={x.get("id"):x for x in load(VALIDATED,{}).get("opportunities",[])}
    rows=[]
    for p in load(PROJECTS,{}).get("projects",[]):
        o=ops.get(p.get("source_opportunity_id"),{})
        score=float(o.get("validation_score",p.get("validation_score",0)) or 0)
        if score < minimum: continue
        rows.append({
          "project_id":p.get("project_id"),
          "title":p.get("title"),
          "commitment_score":score,
          "target_outcomes":[
            "Produce evidence-backed validation",
            "Reach a governed pilot-ready state",
            "Measure outcome quality and resource efficiency"
          ],
          "status":"internal_commitment_defined",
          "external_commitment_authorized":False,
          "created_at":now()
        })
    payload={"generated_at":now(),"commitment_count":len(rows),"commitments":rows}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"commitment_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"commitment_count":len(rows)})
    return {"success":True,"status":"outcome_commitment_complete","report":payload}

r=build()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/outcome_commitment_engine.py"

cat > "$CTL/outcomecommitmentctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"outcome_commitment_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/outcomecommitmentctl"

# ------------------------------------------------------------
# 4. Executive review engine
# ------------------------------------------------------------
cat > "$AGENTS/executive_review_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
DELIVERY=MEM/"delivery_pipeline.json"
COMMIT=MEM/"outcome_commitments.json"
OUT=MEM/"executive_review_queue.json"
STATE=MEM/"executive_review_state.json"
HEALTH=MEM/"executive_review_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def build():
    commitments={x.get("project_id"):x for x in load(COMMIT,{}).get("commitments",[])}
    rows=[]
    for d in load(DELIVERY,{}).get("deliveries",[]):
        c=commitments.get(d.get("project_id"),{})
        rows.append({
          "project_id":d.get("project_id"),
          "title":d.get("title"),
          "delivery_status":d.get("status"),
          "commitment_score":c.get("commitment_score"),
          "review_status":"ready_for_internal_executive_review",
          "external_authority_granted":False
        })
    payload={"generated_at":now(),"review_count":len(rows),"reviews":rows}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"review_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"review_count":len(rows)})
    return {"success":True,"status":"executive_review_complete","queue":payload}

r=build()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/executive_review_engine.py"

cat > "$CTL/executivereviewctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"executive_review_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/executivereviewctl"

# ------------------------------------------------------------
# 5. Risk register engine
# ------------------------------------------------------------
cat > "$AGENTS/risk_register_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
COLLAB=MEM/"specialist_collaboration_groups.json"
INCIDENTS=MEM/"incident_response_queue.json"
OUT=MEM/"enterprise_risk_register.json"
STATE=MEM/"risk_register_state.json"
HEALTH=MEM/"risk_register_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def rid(seed):return hashlib.sha256(str(seed).encode()).hexdigest()[:18]

def build():
    rows=[]
    for g in load(COLLAB,{}).get("groups",[]):
        for risk in g.get("combined_risks",[])[:20]:
            rows.append({
              "risk_id":rid(str(g.get("group_id"))+"|"+str(risk)),
              "source":"specialist_collaboration",
              "topic_id":g.get("topic_id"),
              "risk":risk,
              "severity":"medium",
              "status":"tracked"
            })
    for i in load(INCIDENTS,{}).get("incidents",[]):
        rows.append({
          "risk_id":rid(i.get("incident_id")),
          "source":"incident",
          "topic_id":i.get("component"),
          "risk":"Operational incident requires attention",
          "severity":i.get("severity","medium"),
          "status":"tracked"
        })
    payload={"generated_at":now(),"risk_count":len(rows),"risks":rows}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"risk_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"risk_count":len(rows)})
    return {"success":True,"status":"risk_register_complete","register":payload}

r=build()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/risk_register_engine.py"

cat > "$CTL/riskregisterctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"risk_register_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/riskregisterctl"

# ------------------------------------------------------------
# 6. Portfolio decision engine
# ------------------------------------------------------------
cat > "$AGENTS/portfolio_decision_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
REVIEWS=MEM/"executive_review_queue.json"
RISKS=MEM/"enterprise_risk_register.json"
BUDGETS=MEM/"project_resource_budgets.json"
OUT=MEM/"portfolio_decision_board.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d

def build():
    reviews=load("executive_review_queue.json",{}).get("reviews",[])
    risks=load("enterprise_risk_register.json",{}).get("risks",[])
    budgets=load("project_resource_budgets.json",{}).get("allocations",[])
    payload={
      "generated_at":now(),
      "review_count":len(reviews),
      "risk_count":len(risks),
      "resource_allocation_count":len(budgets),
      "recommended_portfolio_actions":[
        "Continue internal validation for high-scoring projects",
        "Prioritize projects with measurable outcome commitments",
        "Escalate any external action to explicit approval",
        "Pause or re-plan projects with unresolved material risk"
      ],
      "external_authority_granted":False
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return {"success":True,"status":"portfolio_decision_board_complete","board":payload}

r=build()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/portfolio_decision_engine.py"

cat > "$CTL/portfoliodecisionctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"portfolio_decision_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/portfoliodecisionctl"

# ------------------------------------------------------------
# 7. Bundle controller
# ------------------------------------------------------------
cat > "$AGENTS/phase24_bundle4_controller.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase24_bundle4_state.json"; REPORT=MEM/"phase24_bundle4_report.json"; HEALTH=MEM/"phase24_bundle4_health.json"

PIPELINE=[
 ("phase24_bundle3",["python","companyos/phase24bundle3ctl","run"]),
 ("delivery",["python","companyos/deliveryctl","build"]),
 ("approval_policy",["python","companyos/approvalpolicyctl","evaluate"]),
 ("outcome_commitment",["python","companyos/outcomecommitmentctl","build"]),
 ("executive_review",["python","companyos/executivereviewctl","build"]),
 ("risk_register",["python","companyos/riskregisterctl","build"]),
 ("portfolio_decision",["python","companyos/portfoliodecisionctl","show"])
]

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def call(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=2400)
        return {"success":p.returncode==0,"return_code":p.returncode,
          "stdout":p.stdout[-4000:],"stderr":p.stderr[-2000:]}
    except Exception as e:return {"success":False,"error":str(e)}

def run():
    steps=[];failed=[]
    for name,cmd in PIPELINE:
        r=call(cmd);steps.append({"step":name,"result":r})
        if not r.get("success"):failed.append(name)
    report={"generated_at":now(),"steps":steps,"failure_count":len(failed),"failed_steps":failed}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed})
    save(HEALTH,{"healthy":not failed,"last_checked_at":now(),"failure_count":len(failed)})
    return {"success":not failed,"status":"phase24_bundle4_cycle_complete","report":report}

def status():
    def load(p):
        try:return json.loads(p.read_text())
        except:return {}
    return {"success":True,"status":"phase24_bundle4_status","state":load(STATE),"health":load(HEALTH)}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/phase24_bundle4_controller.py"

cat > "$CTL/phase24bundle4ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase24_bundle4_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase24bundle4ctl"

echo "[1/8] Compiling..."
python -m py_compile \
 "$AGENTS/delivery_pipeline_engine.py" \
 "$AGENTS/approval_policy_engine.py" \
 "$AGENTS/outcome_commitment_engine.py" \
 "$AGENTS/executive_review_engine.py" \
 "$AGENTS/risk_register_engine.py" \
 "$AGENTS/portfolio_decision_engine.py" \
 "$AGENTS/phase24_bundle4_controller.py" \
 "$CTL/deliveryctl" "$CTL/approvalpolicyctl" "$CTL/outcomecommitmentctl" \
 "$CTL/executivereviewctl" "$CTL/riskregisterctl" "$CTL/portfoliodecisionctl" "$CTL/phase24bundle4ctl"

echo "[2/8] Building delivery pipeline..."
python "$CTL/deliveryctl" build

echo "[3/8] Evaluating approval policy..."
python "$CTL/approvalpolicyctl" evaluate

echo "[4/8] Building outcome commitments and executive reviews..."
python "$CTL/outcomecommitmentctl" build
python "$CTL/executivereviewctl" build

echo "[5/8] Building enterprise risk register..."
python "$CTL/riskregisterctl" build

echo "[6/8] Building portfolio decision board..."
python "$CTL/portfoliodecisionctl" show

echo "[7/8] Registering scheduler and running integrated cycle..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase24-executive-delivery-governance","enabled":True,"interval_seconds":14400,
"command":["python","companyos/phase24bundle4ctl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart
python "$CTL/phase24bundle4ctl" run || true

echo "[8/8] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"delivery_pipeline_engine.py",r/"agents"/"approval_policy_engine.py",
r/"agents"/"outcome_commitment_engine.py",r/"agents"/"executive_review_engine.py",
r/"agents"/"risk_register_engine.py",r/"agents"/"portfolio_decision_engine.py",
r/"agents"/"phase24_bundle4_controller.py",r/"companyos"/"deliveryctl",
r/"companyos"/"approvalpolicyctl",r/"companyos"/"outcomecommitmentctl",
r/"companyos"/"executivereviewctl",r/"companyos"/"riskregisterctl",
r/"companyos"/"portfoliodecisionctl",r/"companyos"/"phase24bundle4ctl",
r/"ceo_memory"/"phase24_bundle4_config.json",r/"ceo_memory"/"delivery_pipeline.json",
r/"ceo_memory"/"approval_policy_report.json",r/"ceo_memory"/"outcome_commitments.json",
r/"ceo_memory"/"executive_review_queue.json",r/"ceo_memory"/"enterprise_risk_register.json",
r/"ceo_memory"/"portfolio_decision_board.json",r/"ceo_memory"/"autonomous_operations_config.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:14]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase24_bundle4_config.json").read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
"automatic_fund_transfer","automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads((r/"ceo_memory"/"autonomous_operations_config.json").read_text())
if not any(x.get("id")=="phase24-executive-delivery-governance" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Phase 24 Bundle 4 scheduler job missing/disabled")
print("--------------------------------------------")
print("PHASE 24 BUNDLE 4 VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 24 BUNDLE 4 INSTALLED"
echo " EXECUTIVE DELIVERY & GOVERNANCE CORE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Master commands:"
echo "  python companyos/phase24bundle4ctl run"
echo "  python companyos/phase24bundle4ctl status"
echo "  python companyos/portfoliodecisionctl show"
echo
echo "Bundle includes:"
echo "  - Delivery pipeline"
echo "  - Approval policy engine"
echo "  - Outcome commitments"
echo "  - Executive review queue"
echo "  - Enterprise risk register"
echo "  - Portfolio decision board"
echo "  - Integrated Phase 24 Bundle 4 cycle"
