#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase26_authority_execution_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " PHASE 26 - AUTHORITY & EXECUTION CORE"
echo "============================================================"

for f in \
  "$AGENTS/financial_authority_engine.py" \
  "$AGENTS/external_communications_engine.py" \
  "$AGENTS/publication_authority_engine.py" \
  "$AGENTS/production_deployment_engine.py" \
  "$AGENTS/owner_approval_engine.py" \
  "$AGENTS/execution_audit_engine.py" \
  "$AGENTS/phase26_authority_controller.py" \
  "$CTL/financialauthorityctl" \
  "$CTL/communicationsauthorityctl" \
  "$CTL/publicationauthorityctl" \
  "$CTL/deploymentauthorityctl" \
  "$CTL/ownerapprovalctl" \
  "$CTL/executionauditctl" \
  "$CTL/phase26authorityctl"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/authority_execution_config.json" <<'JSON'
{
  "enabled": true,
  "owner_controlled": true,
  "financial_authority": {
    "enabled": true,
    "daily_total_limit_usd": 20000,
    "single_transaction_auto_approval_limit_usd": 15000,
    "above_single_limit_requires_owner_approval": true,
    "above_daily_limit_requires_owner_approval": true,
    "default_deny_on_limit_error": true,
    "audit_all_transactions": true,
    "allowed_asset_classes": ["USD", "USDC", "USDT", "SOL", "ETH"],
    "allowed_accounts": [],
    "blocked_accounts": []
  },
  "communications_authority": {
    "enabled": true,
    "automatic_business_email": true,
    "automatic_customer_messaging": true,
    "automatic_api_messaging": true,
    "contractual_commitments_require_owner_approval": true,
    "legal_admissions_require_owner_approval": true,
    "mass_outreach_requires_owner_approval": true
  },
  "publication_authority": {
    "enabled": true,
    "automatic_publication": true,
    "allowed_targets": [],
    "paid_ad_campaigns_require_owner_approval": true,
    "regulated_claims_require_owner_approval": true
  },
  "deployment_authority": {
    "enabled": true,
    "automatic_deploy_to_approved_targets": true,
    "approved_targets": [],
    "require_tests_before_deploy": true,
    "require_health_check_after_deploy": true,
    "automatic_rollback_on_failure": true,
    "new_production_target_requires_owner_approval": true
  },
  "self_development_authority": {
    "enabled": true,
    "automatic_internal_code_creation": true,
    "automatic_internal_agent_creation": true,
    "automatic_sandbox_testing": true,
    "automatic_internal_promotion_after_tests": true,
    "external_production_promotion_requires_target_authority": true
  }
}
JSON

cat > "$AGENTS/owner_approval_engine.py" <<'PY'
#!/usr/bin/env python3
import json, sys, hashlib, secrets
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
QUEUE=MEM/"owner_approval_queue.json"
STATE=MEM/"owner_approval_state.json"
HEALTH=MEM/"owner_approval_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def aid(seed): return hashlib.sha256((str(seed)+secrets.token_hex(4)).encode()).hexdigest()[:20]

def request(action_class, summary, payload):
    q=load(QUEUE,{"items":[]})
    item={
      "approval_id":aid(summary),
      "action_class":action_class,
      "summary":summary,
      "payload":payload,
      "status":"pending_owner_approval",
      "created_at":now()
    }
    q["items"].append(item);q["updated_at"]=now()
    save(QUEUE,q);save(STATE,{"last_request_at":now(),"pending_count":sum(1 for x in q["items"] if x["status"]=="pending_owner_approval")})
    save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return item

def set_status(approval_id,status):
    q=load(QUEUE,{"items":[]})
    found=None
    for x in q["items"]:
        if x.get("approval_id")==approval_id:
            x["status"]=status;x["resolved_at"]=now();found=x;break
    save(QUEUE,q)
    return found

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="request":
    item=request(sys.argv[2],sys.argv[3],json.loads(sys.argv[4]) if len(sys.argv)>4 else {})
    r={"success":True,"status":"approval_requested","item":item}
elif a in ("approve","deny"):
    found=set_status(sys.argv[2],"approved" if a=="approve" else "denied")
    r={"success":bool(found),"status":"approval_updated","item":found}
else:
    q=load(QUEUE,{"items":[]})
    r={"success":True,"status":"owner_approval_status","queue":q}
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/owner_approval_engine.py"

cat > "$CTL/ownerapprovalctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"owner_approval_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/ownerapprovalctl"

cat > "$AGENTS/financial_authority_engine.py" <<'PY'
#!/usr/bin/env python3
import json, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"authority_execution_config.json"
LEDGER=MEM/"financial_authority_ledger.json"
QUEUE=MEM/"financial_execution_queue.json"
STATE=MEM/"financial_authority_state.json"
HEALTH=MEM/"financial_authority_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def today(): return datetime.now(timezone.utc).date().isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def txid(x): return hashlib.sha256(str(x).encode()).hexdigest()[:20]

def evaluate(amount_usd, source, destination, asset="USD", purpose=""):
    cfg=load(CFG,{})["financial_authority"]
    ledger=load(LEDGER,{"transactions":[]})
    spent=sum(float(x.get("amount_usd",0) or 0) for x in ledger["transactions"] if x.get("date")==today() and x.get("status")=="executed")
    reasons=[]
    requires=False
    if amount_usd > float(cfg["single_transaction_auto_approval_limit_usd"]):
        requires=True;reasons.append("single_transaction_limit")
    if spent + amount_usd > float(cfg["daily_total_limit_usd"]):
        requires=True;reasons.append("daily_total_limit")
    if cfg.get("allowed_accounts") and destination not in cfg["allowed_accounts"]:
        requires=True;reasons.append("destination_not_preapproved")
    if destination in cfg.get("blocked_accounts",[]):
        return {"allowed":False,"requires_owner_approval":False,"reason":["blocked_destination"]}
    if asset not in cfg.get("allowed_asset_classes",[]):
        requires=True;reasons.append("asset_not_preapproved")
    return {
      "allowed":not requires,
      "requires_owner_approval":requires,
      "reasons":reasons,
      "daily_spent_usd":spent,
      "daily_remaining_usd":max(0,float(cfg["daily_total_limit_usd"])-spent),
      "single_auto_limit_usd":cfg["single_transaction_auto_approval_limit_usd"]
    }

def queue(amount_usd,source,destination,asset,purpose):
    decision=evaluate(amount_usd,source,destination,asset,purpose)
    q=load(QUEUE,{"items":[]})
    item={
      "transaction_id":txid(f"{now()}|{source}|{destination}|{amount_usd}"),
      "amount_usd":amount_usd,"source":source,"destination":destination,"asset":asset,"purpose":purpose,
      "authority_decision":decision,
      "status":"ready_for_connector_execution" if decision["allowed"] else ("pending_owner_approval" if decision["requires_owner_approval"] else "blocked"),
      "created_at":now()
    }
    q["items"].append(item);save(QUEUE,q)
    save(STATE,{"last_evaluated_at":now(),"queued_count":len(q["items"])})
    save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return item

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="evaluate":
    r={"success":True,"decision":evaluate(float(sys.argv[2]),sys.argv[3],sys.argv[4],sys.argv[5] if len(sys.argv)>5 else "USD"," ".join(sys.argv[6:]) if len(sys.argv)>6 else "")}
elif a=="queue":
    item=queue(float(sys.argv[2]),sys.argv[3],sys.argv[4],sys.argv[5] if len(sys.argv)>5 else "USD"," ".join(sys.argv[6:]) if len(sys.argv)>6 else "")
    r={"success":True,"status":"financial_action_queued","item":item}
else:
    r={"success":True,"status":"financial_authority_status","state":load(STATE,{}),"queue":load(QUEUE,{"items":[]}),"ledger":load(LEDGER,{"transactions":[]})}
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/financial_authority_engine.py"

cat > "$CTL/financialauthorityctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"financial_authority_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/financialauthorityctl"

cat > "$AGENTS/external_communications_engine.py" <<'PY'
#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
CFG=MEM/"authority_execution_config.json";OUT=MEM/"communications_execution_queue.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):p.write_text(json.dumps(d,indent=2))
def run():
    cfg=load(CFG,{})["communications_authority"]
    payload={"generated_at":now(),"enabled":cfg.get("enabled"),"capabilities":{
      "business_email":cfg.get("automatic_business_email"),
      "customer_messaging":cfg.get("automatic_customer_messaging"),
      "api_messaging":cfg.get("automatic_api_messaging"),
      "contractual_commitments_require_owner_approval":cfg.get("contractual_commitments_require_owner_approval"),
      "mass_outreach_requires_owner_approval":cfg.get("mass_outreach_requires_owner_approval")
    },"status":"connector_ready"}
    save(OUT,payload);return {"success":True,"status":"communications_authority_complete","report":payload}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/external_communications_engine.py"

cat > "$CTL/communicationsauthorityctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"external_communications_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/communicationsauthorityctl"

cat > "$AGENTS/publication_authority_engine.py" <<'PY'
#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
CFG=MEM/"authority_execution_config.json";OUT=MEM/"publication_authority_report.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def run():
    c=load(CFG,{})["publication_authority"]
    r={"generated_at":now(),"enabled":c.get("enabled"),"automatic_publication":c.get("automatic_publication"),
       "allowed_targets":c.get("allowed_targets",[]),"paid_ad_campaigns_require_owner_approval":c.get("paid_ad_campaigns_require_owner_approval"),
       "regulated_claims_require_owner_approval":c.get("regulated_claims_require_owner_approval")}
    OUT.write_text(json.dumps(r,indent=2));return {"success":True,"status":"publication_authority_complete","report":r}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/publication_authority_engine.py"

cat > "$CTL/publicationauthorityctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"publication_authority_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/publicationauthorityctl"

cat > "$AGENTS/production_deployment_engine.py" <<'PY'
#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
CFG=MEM/"authority_execution_config.json";OUT=MEM/"deployment_authority_report.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def run():
    c=load(CFG,{})["deployment_authority"]
    r={"generated_at":now(),"enabled":c.get("enabled"),
       "automatic_deploy_to_approved_targets":c.get("automatic_deploy_to_approved_targets"),
       "approved_targets":c.get("approved_targets",[]),
       "require_tests_before_deploy":c.get("require_tests_before_deploy"),
       "require_health_check_after_deploy":c.get("require_health_check_after_deploy"),
       "automatic_rollback_on_failure":c.get("automatic_rollback_on_failure"),
       "new_production_target_requires_owner_approval":c.get("new_production_target_requires_owner_approval")}
    OUT.write_text(json.dumps(r,indent=2));return {"success":True,"status":"deployment_authority_complete","report":r}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/production_deployment_engine.py"

cat > "$CTL/deploymentauthorityctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"production_deployment_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/deploymentauthorityctl"

cat > "$AGENTS/execution_audit_engine.py" <<'PY'
#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
OUT=MEM/"execution_authority_audit.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text())
    except:return d
def run():
    r={"generated_at":now(),
       "financial_queue":load("financial_execution_queue.json",{"items":[]}),
       "approvals":load("owner_approval_queue.json",{"items":[]}),
       "communications":load("communications_execution_queue.json",{}),
       "publication":load("publication_authority_report.json",{}),
       "deployment":load("deployment_authority_report.json",{})}
    OUT.write_text(json.dumps(r,indent=2));return {"success":True,"status":"execution_audit_complete","report":r}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/execution_audit_engine.py"

cat > "$CTL/executionauditctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"execution_audit_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/executionauditctl"

cat > "$AGENTS/phase26_authority_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
STATE=MEM/"phase26_authority_state.json";REPORT=MEM/"phase26_authority_report.json";HEALTH=MEM/"phase26_authority_health.json"
PIPELINE=[
 ("communications",["python","companyos/communicationsauthorityctl"]),
 ("publication",["python","companyos/publicationauthorityctl"]),
 ("deployment",["python","companyos/deploymentauthorityctl"]),
 ("audit",["python","companyos/executionauditctl"])
]
def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run():
    steps=[];failed=[]
    for name,cmd in PIPELINE:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=600)
        r={"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-2500:],"stderr":p.stderr[-1000:]}
        steps.append({"step":name,"result":r})
        if not r["success"]:failed.append(name)
    report={"generated_at":now(),"failure_count":len(failed),"failed_steps":failed,"steps":steps}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now()})
    return {"success":not failed,"status":"phase26_authority_cycle_complete","report":report}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/phase26_authority_controller.py"

cat > "$CTL/phase26authorityctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase26_authority_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase26authorityctl"

echo "[1/7] Compiling..."
python -m py_compile \
 "$AGENTS/financial_authority_engine.py" "$AGENTS/external_communications_engine.py" \
 "$AGENTS/publication_authority_engine.py" "$AGENTS/production_deployment_engine.py" \
 "$AGENTS/owner_approval_engine.py" "$AGENTS/execution_audit_engine.py" \
 "$AGENTS/phase26_authority_controller.py" \
 "$CTL/financialauthorityctl" "$CTL/communicationsauthorityctl" "$CTL/publicationauthorityctl" \
 "$CTL/deploymentauthorityctl" "$CTL/ownerapprovalctl" "$CTL/executionauditctl" "$CTL/phase26authorityctl"

echo "[2/7] Initializing financial authority..."
python "$CTL/financialauthorityctl" evaluate 1000 demo-source demo-destination USD internal-test

echo "[3/7] Communications authority..."
python "$CTL/communicationsauthorityctl"

echo "[4/7] Publication + deployment authority..."
python "$CTL/publicationauthorityctl"
python "$CTL/deploymentauthorityctl"

echo "[5/7] Execution audit..."
python "$CTL/executionauditctl"

echo "[6/7] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase26-authority-execution-core","enabled":True,"interval_seconds":7200,
     "command":["python","companyos/phase26authorityctl"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart

echo "[7/7] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"financial_authority_engine.py",r/"agents"/"external_communications_engine.py",
r/"agents"/"publication_authority_engine.py",r/"agents"/"production_deployment_engine.py",
r/"agents"/"owner_approval_engine.py",r/"agents"/"execution_audit_engine.py",
r/"agents"/"phase26_authority_controller.py",r/"companyos"/"financialauthorityctl",
r/"companyos"/"communicationsauthorityctl",r/"companyos"/"publicationauthorityctl",
r/"companyos"/"deploymentauthorityctl",r/"companyos"/"ownerapprovalctl",
r/"companyos"/"executionauditctl",r/"companyos"/"phase26authorityctl",
r/"ceo_memory"/"authority_execution_config.json",r/"ceo_memory"/"autonomous_operations_config.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:14]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"authority_execution_config.json").read_text())
fa=cfg["financial_authority"]
if fa.get("daily_total_limit_usd") != 20000:errors.append("Daily limit must be 20000")
if fa.get("single_transaction_auto_approval_limit_usd") != 15000:errors.append("Single auto-approval limit must be 15000")
if not fa.get("above_single_limit_requires_owner_approval"):errors.append("Single-limit owner approval must be enabled")
if not fa.get("above_daily_limit_requires_owner_approval"):errors.append("Daily-limit owner approval must be enabled")
print("--------------------------------------------")
print("PHASE 26 AUTHORITY CORE VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 26 AUTHORITY & EXECUTION CORE INSTALLED"
echo " FINANCIAL / COMMUNICATION / PUBLICATION / DEPLOYMENT AUTHORITY ACTIVE"
echo " DAILY FINANCIAL LIMIT: \$20,000"
echo " SINGLE AUTO TRANSACTION LIMIT: \$15,000"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Important:"
echo "  This bundle creates the authority/governance layer."
echo "  Real fund transfers, email sends, publication, and deployments require connector credentials/configuration."
echo
echo "Commands:"
echo "  python companyos/financialauthorityctl status"
echo "  python companyos/financialauthorityctl evaluate 10000 SOURCE DEST USD purpose"
echo "  python companyos/ownerapprovalctl status"
echo "  python companyos/phase26authorityctl"
