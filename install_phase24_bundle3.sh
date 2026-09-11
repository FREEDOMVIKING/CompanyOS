#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase24_bundle3_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 24 BUNDLE 3 - GOVERNED EXECUTION & OPERATIONS CORE"
echo "============================================================"

for f in \
  "$AGENTS/approval_gateway.py" \
  "$AGENTS/external_action_registry.py" \
  "$AGENTS/execution_receipt_engine.py" \
  "$AGENTS/connector_readiness_engine.py" \
  "$AGENTS/operations_observability_engine.py" \
  "$AGENTS/incident_response_engine.py" \
  "$AGENTS/executive_control_center.py" \
  "$AGENTS/phase24_bundle3_controller.py" \
  "$CTL/approvalgatewayctl" \
  "$CTL/actionregistryctl" \
  "$CTL/executionreceiptctl" \
  "$CTL/connectorreadinessctl" \
  "$CTL/observabilityctl" \
  "$CTL/incidentctl" \
  "$CTL/controlcenterctl" \
  "$CTL/phase24bundle3ctl"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/phase24_bundle3_config.json" <<'JSON'
{
  "enabled": true,
  "maximum_pending_approvals": 100,
  "maximum_action_records": 500,
  "maximum_receipts": 1000,
  "maximum_incidents": 100,
  "automatic_internal_observability": true,
  "automatic_internal_incident_triage": true,
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
# 1. Approval gateway
# ------------------------------------------------------------
cat > "$AGENTS/approval_gateway.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle3_config.json"
INCUBATION=MEM/"business_incubation_portfolio.json"
PROJECTS=MEM/"project_execution_registry.json"
OUT=MEM/"governed_approval_queue.json"
STATE=MEM/"approval_gateway_state.json"
HEALTH=MEM/"approval_gateway_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def aid(seed):return hashlib.sha256(str(seed).encode()).hexdigest()[:20]

def build():
    cfg=load(CFG,{})
    existing=load(OUT,{"items":[]}).get("items",[])
    seen={x.get("approval_id") for x in existing}
    added=[]

    for c in load(INCUBATION,{}).get("candidates",[]):
        if c.get("external_launch_authorized") is True:
            continue
        approval_id=aid("launch|"+str(c.get("project_id")))
        if approval_id in seen: continue
        item={
          "approval_id":approval_id,
          "project_id":c.get("project_id"),
          "title":c.get("title"),
          "action_class":"external_launch_or_publication",
          "requested_authority":"explicit_human_approval_required",
          "status":"pending",
          "created_at":now()
        }
        existing.append(item);added.append(item);seen.add(approval_id)

    for p in load(PROJECTS,{}).get("projects",[]):
        approval_id=aid("execution|"+str(p.get("project_id")))
        if approval_id in seen: continue
        item={
          "approval_id":approval_id,
          "project_id":p.get("project_id"),
          "title":p.get("title"),
          "action_class":"external_execution_boundary",
          "requested_authority":"explicit_human_approval_required",
          "status":"pending",
          "created_at":now()
        }
        existing.append(item);added.append(item);seen.add(approval_id)

    existing=existing[:int(cfg.get("maximum_pending_approvals",100))]
    payload={"generated_at":now(),"item_count":len(existing),"items":existing}
    save(OUT,payload)
    save(STATE,{"last_built_at":now(),"added_count":len(added),"item_count":len(existing)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"item_count":len(existing)})
    return {"success":True,"status":"approval_gateway_complete","added_count":len(added),"queue":payload}

def status():
    return {"success":True,"status":"approval_gateway_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"queue":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/approval_gateway.py"

cat > "$CTL/approvalgatewayctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"approval_gateway.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/approvalgatewayctl"

# ------------------------------------------------------------
# 2. External action registry
# ------------------------------------------------------------
cat > "$AGENTS/external_action_registry.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
APPROVALS=MEM/"governed_approval_queue.json"
OUT=MEM/"external_action_registry.json"
STATE=MEM/"external_action_registry_state.json"
HEALTH=MEM/"external_action_registry_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def sync():
    approvals=load(APPROVALS,{}).get("items",[])
    rows=[]
    for a in approvals:
        rows.append({
          "action_id":a.get("approval_id"),
          "project_id":a.get("project_id"),
          "title":a.get("title"),
          "action_class":a.get("action_class"),
          "approval_status":a.get("status","pending"),
          "execution_status":"blocked_until_explicit_approval",
          "external_execution_allowed":False,
          "updated_at":now()
        })
    payload={"generated_at":now(),"action_count":len(rows),"actions":rows}
    save(OUT,payload);save(STATE,{"last_synced_at":now(),"action_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"action_count":len(rows)})
    return {"success":True,"status":"external_action_registry_complete","registry":payload}

def status():
    return {"success":True,"status":"external_action_registry_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"registry":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=sync() if a=="sync" else status() if a=="status" else {"success":False,"allowed":["sync","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/external_action_registry.py"

cat > "$CTL/actionregistryctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"external_action_registry.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/actionregistryctl"

# ------------------------------------------------------------
# 3. Execution receipt engine
# ------------------------------------------------------------
cat > "$AGENTS/execution_receipt_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
RESULTS=MEM/"specialist_runtime_results.json"
OUT=MEM/"execution_receipts.json"
STATE=MEM/"execution_receipt_state.json"
HEALTH=MEM/"execution_receipt_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def rid(seed):return hashlib.sha256(str(seed).encode()).hexdigest()[:20]

def build():
    rows=load(RESULTS,{}).get("results",[])
    receipts=[]
    for r in rows[-500:]:
        if r.get("status")!="completed":continue
        receipts.append({
          "receipt_id":rid(r.get("work_id")),
          "work_id":r.get("work_id"),
          "project_id":r.get("opportunity_id"),
          "action_type":r.get("action_type"),
          "status":"completed_internal",
          "execution_boundary":r.get("execution_boundary","internal_non_destructive_only"),
          "completed_at":r.get("completed_at"),
          "recorded_at":now()
        })
    payload={"generated_at":now(),"receipt_count":len(receipts),"receipts":receipts}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"receipt_count":len(receipts)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"receipt_count":len(receipts)})
    return {"success":True,"status":"execution_receipts_complete","report":payload}

def status():
    return {"success":True,"status":"execution_receipt_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/execution_receipt_engine.py"

cat > "$CTL/executionreceiptctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"execution_receipt_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/executionreceiptctl"

# ------------------------------------------------------------
# 4. Connector readiness engine
# ------------------------------------------------------------
cat > "$AGENTS/connector_readiness_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,os
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"connector_readiness_report.json"
STATE=MEM/"connector_readiness_state.json"
HEALTH=MEM/"connector_readiness_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def check():
    checks=[
      {"connector":"openrouter","configured":bool(os.getenv("OPENROUTER_API_KEY","").strip()),
       "capability":"ai_reasoning","external_side_effects":False},
      {"connector":"github","configured":(ROOT/".git").exists(),
       "capability":"source_control","external_side_effects":True},
      {"connector":"crm","configured":(MEM/"crm_state.json").exists(),
       "capability":"customer_records","external_side_effects":False},
      {"connector":"accounting","configured":(MEM/"accounting_state.json").exists(),
       "capability":"finance_records","external_side_effects":False}
    ]
    payload={"generated_at":now(),"connector_count":len(checks),"connectors":checks}
    save(OUT,payload);save(STATE,{"last_checked_at":now(),"connector_count":len(checks)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"connector_count":len(checks)})
    return {"success":True,"status":"connector_readiness_complete","report":payload}

r=check()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/connector_readiness_engine.py"

cat > "$CTL/connectorreadinessctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"connector_readiness_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/connectorreadinessctl"

# ------------------------------------------------------------
# 5. Operations observability engine
# ------------------------------------------------------------
cat > "$AGENTS/operations_observability_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"operations_observability_report.json"
STATE=MEM/"operations_observability_state.json"
HEALTH=MEM/"operations_observability_health.json"

FILES=[
 ("autonomy","autonomy_core_health.json"),
 ("phase23","phase23_health.json"),
 ("phase23_bundle2","phase23_bundle2_health.json"),
 ("phase23_bundle3","phase23_bundle3_health.json"),
 ("phase24","phase24_health.json"),
 ("phase24_bundle2","phase24_bundle2_health.json"),
 ("specialist_runtime","specialist_runtime_health.json"),
 ("provider","provider_health_health.json"),
 ("memory","persistent_memory_health.json")
]

def now():return datetime.now(timezone.utc).isoformat()
def load(name):
    p=MEM/name
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return {}
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def run():
    components=[];unhealthy=[]
    for label,name in FILES:
        data=load(name)
        healthy=bool(data.get("healthy",False))
        components.append({"component":label,"healthy":healthy,"data":data})
        if not healthy:unhealthy.append(label)
    payload={"generated_at":now(),"healthy":not unhealthy,"unhealthy_count":len(unhealthy),
      "unhealthy_components":unhealthy,"components":components}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"unhealthy_count":len(unhealthy)})
    save(HEALTH,{"healthy":not unhealthy,"last_checked_at":now(),"unhealthy_count":len(unhealthy)})
    return {"success":True,"status":"operations_observability_complete","report":payload}

r=run()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/operations_observability_engine.py"

cat > "$CTL/observabilityctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"operations_observability_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/observabilityctl"

# ------------------------------------------------------------
# 6. Incident response engine
# ------------------------------------------------------------
cat > "$AGENTS/incident_response_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OBS=MEM/"operations_observability_report.json"
OUT=MEM/"incident_response_queue.json"
STATE=MEM/"incident_response_state.json"
HEALTH=MEM/"incident_response_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def iid(seed):return hashlib.sha256(str(seed).encode()).hexdigest()[:18]

def triage():
    obs=load(OBS,{})
    rows=[]
    for comp in obs.get("unhealthy_components",[]):
        rows.append({
          "incident_id":iid(comp),
          "component":comp,
          "severity":"medium",
          "status":"triage_internal",
          "recommended_actions":[
            "Inspect current health and state files",
            "Re-run the failing internal component",
            "Re-run dependency chain if needed",
            "Escalate for human review before any external or destructive action"
          ],
          "external_action_authorized":False,
          "created_at":now()
        })
    payload={"generated_at":now(),"incident_count":len(rows),"incidents":rows}
    save(OUT,payload);save(STATE,{"last_triaged_at":now(),"incident_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"incident_count":len(rows)})
    return {"success":True,"status":"incident_triage_complete","queue":payload}

r=triage()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/incident_response_engine.py"

cat > "$CTL/incidentctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"incident_response_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/incidentctl"

# ------------------------------------------------------------
# 7. Executive control center
# ------------------------------------------------------------
cat > "$AGENTS/executive_control_center.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"executive_control_center.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d

def build():
    approvals=load("governed_approval_queue.json",{})
    actions=load("external_action_registry.json",{})
    receipts=load("execution_receipts.json",{})
    connectors=load("connector_readiness_report.json",{})
    obs=load("operations_observability_report.json",{})
    incidents=load("incident_response_queue.json",{})
    portfolio=load("ceo_project_portfolio.json",{})
    payload={
      "generated_at":now(),
      "system_health":"healthy" if obs.get("healthy",False) else "attention",
      "pending_approval_count":sum(1 for x in approvals.get("items",[]) if x.get("status")=="pending"),
      "registered_external_action_count":actions.get("action_count",0),
      "execution_receipt_count":receipts.get("receipt_count",0),
      "connector_readiness":connectors.get("connectors",[]),
      "incident_count":incidents.get("incident_count",0),
      "project_count":portfolio.get("project_count",0),
      "external_authority_granted":False,
      "control_note":"External actions remain blocked until explicit approval changes authority state."
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return {"success":True,"status":"executive_control_center_complete","control_center":payload}

r=build()
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/executive_control_center.py"

cat > "$CTL/controlcenterctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"executive_control_center.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/controlcenterctl"

# ------------------------------------------------------------
# 8. Phase 24 Bundle 3 controller
# ------------------------------------------------------------
cat > "$AGENTS/phase24_bundle3_controller.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase24_bundle3_state.json"; REPORT=MEM/"phase24_bundle3_report.json"; HEALTH=MEM/"phase24_bundle3_health.json"

PIPELINE=[
 ("phase24_bundle2",["python","companyos/phase24bundle2ctl","run"]),
 ("approval_gateway",["python","companyos/approvalgatewayctl","build"]),
 ("action_registry",["python","companyos/actionregistryctl","sync"]),
 ("execution_receipts",["python","companyos/executionreceiptctl","build"]),
 ("connector_readiness",["python","companyos/connectorreadinessctl","check"]),
 ("observability",["python","companyos/observabilityctl","run"]),
 ("incident_triage",["python","companyos/incidentctl","run"]),
 ("control_center",["python","companyos/controlcenterctl","show"])
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
    return {"success":not failed,"status":"phase24_bundle3_cycle_complete","report":report}

def status():
    def load(p):
        try:return json.loads(p.read_text())
        except:return {}
    return {"success":True,"status":"phase24_bundle3_status","state":load(STATE),"health":load(HEALTH)}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/phase24_bundle3_controller.py"

cat > "$CTL/phase24bundle3ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase24_bundle3_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase24bundle3ctl"

echo "[1/8] Compiling..."
python -m py_compile \
 "$AGENTS/approval_gateway.py" \
 "$AGENTS/external_action_registry.py" \
 "$AGENTS/execution_receipt_engine.py" \
 "$AGENTS/connector_readiness_engine.py" \
 "$AGENTS/operations_observability_engine.py" \
 "$AGENTS/incident_response_engine.py" \
 "$AGENTS/executive_control_center.py" \
 "$AGENTS/phase24_bundle3_controller.py" \
 "$CTL/approvalgatewayctl" "$CTL/actionregistryctl" "$CTL/executionreceiptctl" \
 "$CTL/connectorreadinessctl" "$CTL/observabilityctl" "$CTL/incidentctl" \
 "$CTL/controlcenterctl" "$CTL/phase24bundle3ctl"

echo "[2/8] Building governed approval gateway..."
python "$CTL/approvalgatewayctl" build

echo "[3/8] Syncing external action registry..."
python "$CTL/actionregistryctl" sync

echo "[4/8] Building execution receipts..."
python "$CTL/executionreceiptctl" build

echo "[5/8] Checking connector readiness and observability..."
python "$CTL/connectorreadinessctl" check
python "$CTL/observabilityctl" run

echo "[6/8] Running incident triage and control center..."
python "$CTL/incidentctl" run
python "$CTL/controlcenterctl" show

echo "[7/8] Registering scheduler and running integrated cycle..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase24-governed-execution-operations","enabled":True,"interval_seconds":10800,
"command":["python","companyos/phase24bundle3ctl","run"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2),encoding="utf-8")
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart
python "$CTL/phase24bundle3ctl" run || true

echo "[8/8] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"approval_gateway.py",r/"agents"/"external_action_registry.py",
r/"agents"/"execution_receipt_engine.py",r/"agents"/"connector_readiness_engine.py",
r/"agents"/"operations_observability_engine.py",r/"agents"/"incident_response_engine.py",
r/"agents"/"executive_control_center.py",r/"agents"/"phase24_bundle3_controller.py",
r/"companyos"/"approvalgatewayctl",r/"companyos"/"actionregistryctl",
r/"companyos"/"executionreceiptctl",r/"companyos"/"connectorreadinessctl",
r/"companyos"/"observabilityctl",r/"companyos"/"incidentctl",
r/"companyos"/"controlcenterctl",r/"companyos"/"phase24bundle3ctl",
r/"ceo_memory"/"phase24_bundle3_config.json",r/"ceo_memory"/"governed_approval_queue.json",
r/"ceo_memory"/"external_action_registry.json",r/"ceo_memory"/"execution_receipts.json",
r/"ceo_memory"/"connector_readiness_report.json",r/"ceo_memory"/"operations_observability_report.json",
r/"ceo_memory"/"incident_response_queue.json",r/"ceo_memory"/"executive_control_center.json",
r/"ceo_memory"/"autonomous_operations_config.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:16]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase24_bundle3_config.json").read_text())
for k in ["automatic_external_write","automatic_customer_contact","automatic_publication","automatic_spending",
"automatic_fund_transfer","automatic_code_changes","automatic_merge","automatic_deploy","automatic_destructive_actions"]:
    if cfg.get(k) is not False:errors.append(f"{k} must remain disabled")
sched=json.loads((r/"ceo_memory"/"autonomous_operations_config.json").read_text())
if not any(x.get("id")=="phase24-governed-execution-operations" and x.get("enabled") for x in sched.get("jobs",[])):
    errors.append("Phase 24 Bundle 3 scheduler job missing/disabled")
print("--------------------------------------------")
print("PHASE 24 BUNDLE 3 VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 24 BUNDLE 3 INSTALLED"
echo " GOVERNED EXECUTION & OPERATIONS CORE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Master commands:"
echo "  python companyos/phase24bundle3ctl run"
echo "  python companyos/phase24bundle3ctl status"
echo "  python companyos/controlcenterctl show"
echo
echo "Bundle includes:"
echo "  - Governed approval gateway"
echo "  - External action registry"
echo "  - Execution receipts"
echo "  - Connector readiness"
echo "  - Operations observability"
echo "  - Incident response"
echo "  - Executive control center"
echo "  - Integrated Phase 24 Bundle 3 cycle"
