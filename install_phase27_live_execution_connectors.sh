#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
CONN="$ROOT/connectors"
LOGS="$ROOT/logs"
BACKUP="$ROOT/backups/phase27_execution_connectors_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$CONN" "$LOGS" "$BACKUP"

echo "============================================================"
echo " PHASE 27 - LIVE EXECUTION CONNECTOR CORE"
echo "============================================================"

cat > "$MEM/phase27_execution_config.json" <<'JSON'
{
  "enabled": true,
  "financial": {
    "daily_total_limit_usd": 20000,
    "single_transaction_auto_approval_limit_usd": 15000,
    "connector_mode": "configured_only",
    "require_balance_check": true,
    "require_destination_allowlist_or_owner_approval": true,
    "require_audit_log": true
  },
  "communications": {
    "enabled": true,
    "connector_mode": "configured_only",
    "require_identity_profile": true,
    "contractual_commitments_require_owner_approval": true,
    "mass_outreach_requires_owner_approval": true
  },
  "publication": {
    "enabled": true,
    "connector_mode": "configured_only",
    "require_target_registration": true,
    "paid_campaigns_require_owner_approval": true
  },
  "deployment": {
    "enabled": true,
    "connector_mode": "configured_only",
    "require_target_registration": true,
    "require_tests": true,
    "require_health_check": true,
    "automatic_rollback": true
  }
}
JSON

cat > "$MEM/connector_registry.json" <<'JSON'
{
  "connectors": [],
  "note": "No connector executes until explicitly configured with credentials and a registered target/account."
}
JSON

cat > "$AGENTS/connector_registry_engine.py" <<'PY'
#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
REG=MEM/"connector_registry.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load():
    try:return json.loads(REG.read_text())
    except:return {"connectors":[]}
def save(d): REG.write_text(json.dumps(d,indent=2))
def cid(kind,name): return hashlib.sha256(f"{kind}|{name}".encode()).hexdigest()[:18]

a=sys.argv[1] if len(sys.argv)>1 else "list"
d=load()

if a=="register":
    kind,name=sys.argv[2],sys.argv[3]
    c={
      "connector_id":cid(kind,name),
      "kind":kind,
      "name":name,
      "enabled":False,
      "configured":False,
      "credential_env":None,
      "target":None,
      "created_at":now()
    }
    d["connectors"]=[x for x in d.get("connectors",[]) if x.get("connector_id")!=c["connector_id"]]+[c]
    save(d); r={"success":True,"status":"connector_registered","connector":c}
elif a=="configure":
    connector_id,credential_env,target=sys.argv[2],sys.argv[3],sys.argv[4]
    found=None
    for c in d.get("connectors",[]):
        if c.get("connector_id")==connector_id:
            c["credential_env"]=credential_env;c["target"]=target;c["configured"]=True;c["updated_at"]=now();found=c
    save(d);r={"success":bool(found),"status":"connector_configured","connector":found}
elif a=="enable":
    connector_id=sys.argv[2];found=None
    for c in d.get("connectors",[]):
        if c.get("connector_id")==connector_id:
            c["enabled"]=bool(c.get("configured"));c["updated_at"]=now();found=c
    save(d);r={"success":bool(found and found.get("enabled")),"status":"connector_enable_result","connector":found}
else:
    r={"success":True,"status":"connector_registry","registry":d}
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/connector_registry_engine.py"

cat > "$CTL/connectorregistryctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"connector_registry_engine.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/connectorregistryctl"

cat > "$AGENTS/live_execution_router.py" <<'PY'
#!/usr/bin/env python3
import json,os,sys,subprocess
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"; LOG=ROOT/"logs"/"live_execution_audit.jsonl"
REG=MEM/"connector_registry.json"; AUTH=MEM/"authority_execution_config.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def audit(x):
    LOG.parent.mkdir(parents=True,exist_ok=True)
    with LOG.open("a") as f:f.write(json.dumps(x)+"\n")

def connectors(kind):
    return [c for c in load(REG,{"connectors":[]}).get("connectors",[]) if c.get("kind")==kind and c.get("enabled") and c.get("configured")]

def route(kind,payload):
    cs=connectors(kind)
    if not cs:
        r={"success":False,"status":"no_configured_connector","kind":kind,"payload":payload,"executed":False}
        audit({"at":now(),**r});return r
    c=cs[0]
    key=os.getenv(c.get("credential_env") or "","")
    if not key:
        r={"success":False,"status":"credential_unavailable","connector_id":c.get("connector_id"),"executed":False}
        audit({"at":now(),**r});return r
    # Connector execution is adapter-driven. This core never improvises a protocol.
    adapter=ROOT/"connectors"/f"{kind}_adapter.py"
    if not adapter.exists():
        r={"success":False,"status":"adapter_missing","connector_id":c.get("connector_id"),"executed":False}
        audit({"at":now(),**r});return r
    p=subprocess.run([sys.executable,str(adapter),json.dumps({"connector":c,"payload":payload})],
                     cwd=ROOT,text=True,capture_output=True,timeout=300)
    r={"success":p.returncode==0,"status":"connector_execution_complete" if p.returncode==0 else "connector_execution_failed",
       "connector_id":c.get("connector_id"),"stdout":p.stdout[-3000:],"stderr":p.stderr[-1000:],"executed":p.returncode==0}
    audit({"at":now(),"kind":kind,"payload":payload,**r});return r

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="execute":
    kind=sys.argv[2]; payload=json.loads(sys.argv[3]); r=route(kind,payload)
else:
    r={"success":True,"status":"live_execution_router_ready","registered_connectors":load(REG,{"connectors":[]})}
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/live_execution_router.py"

cat > "$CTL/liveexecutionctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"live_execution_router.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/liveexecutionctl"

cat > "$AGENTS/financial_execution_bridge.py" <<'PY'
#!/usr/bin/env python3
import json,sys,subprocess
from pathlib import Path

ROOT=Path.home()/"companyos"
def call(args):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=120)
    try:return json.loads(p.stdout)
    except:return {"success":False,"raw":p.stdout,"stderr":p.stderr}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="queue":
    amount=float(sys.argv[2]);source=sys.argv[3];dest=sys.argv[4];asset=sys.argv[5] if len(sys.argv)>5 else "USD";purpose=" ".join(sys.argv[6:])
    decision=call([sys.executable,"companyos/financialauthorityctl","evaluate",str(amount),source,dest,asset,purpose])
    d=decision.get("decision",{})
    if not d.get("allowed"):
        r={"success":True,"status":"pending_owner_approval" if d.get("requires_owner_approval") else "blocked","decision":d,"executed":False}
    else:
        payload={"amount_usd":amount,"source":source,"destination":dest,"asset":asset,"purpose":purpose}
        r=call([sys.executable,"companyos/liveexecutionctl","execute","financial",json.dumps(payload)])
else:r={"success":True,"status":"financial_execution_bridge_ready"}
print(json.dumps(r,indent=2))
PY
chmod +x "$AGENTS/financial_execution_bridge.py"

cat > "$CTL/financialexecutionctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"financial_execution_bridge.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/financialexecutionctl"

cat > "$AGENTS/external_action_bridge.py" <<'PY'
#!/usr/bin/env python3
import json,sys,subprocess
from pathlib import Path
ROOT=Path.home()/"companyos"
kind=sys.argv[1] if len(sys.argv)>1 else "status"
if kind=="status":
    print(json.dumps({"success":True,"status":"external_action_bridge_ready"},indent=2));raise SystemExit(0)
payload=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
p=subprocess.run([sys.executable,"companyos/liveexecutionctl","execute",kind,json.dumps(payload)],cwd=ROOT,text=True,capture_output=True,timeout=300)
print(p.stdout or json.dumps({"success":False,"stderr":p.stderr},indent=2))
raise SystemExit(p.returncode)
PY
chmod +x "$AGENTS/external_action_bridge.py"

cat > "$CTL/externalactionctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"external_action_bridge.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/externalactionctl"

# Safe adapter templates. They fail closed until the user replaces/configures them for a specific service.
for kind in financial communications publication deployment; do
cat > "$CONN/${kind}_adapter.py" <<PY
#!/usr/bin/env python3
import json,sys
req=json.loads(sys.argv[1]) if len(sys.argv)>1 else {}
print(json.dumps({
  "success": False,
  "status": "adapter_not_configured",
  "kind": "$kind",
  "message": "Configure this adapter for a specific approved provider/target before live execution."
}, indent=2))
raise SystemExit(2)
PY
chmod +x "$CONN/${kind}_adapter.py"
done

cat > "$AGENTS/phase27_controller.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
STATE=MEM/"phase27_state.json";HEALTH=MEM/"phase27_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run():
    p=subprocess.run([sys.executable,"companyos/liveexecutionctl","status"],cwd=ROOT,text=True,capture_output=True,timeout=60)
    ok=p.returncode==0
    save(STATE,{"last_run_at":now(),"failure_count":0 if ok else 1})
    save(HEALTH,{"healthy":ok,"last_checked_at":now()})
    return {"success":ok,"status":"phase27_execution_connector_core_ready","router":p.stdout}
print(json.dumps(run(),indent=2))
PY
chmod +x "$AGENTS/phase27_controller.py"

cat > "$CTL/phase27ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase27_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase27ctl"

echo "[1/6] Compiling..."
python -m py_compile \
 "$AGENTS/connector_registry_engine.py" "$AGENTS/live_execution_router.py" \
 "$AGENTS/financial_execution_bridge.py" "$AGENTS/external_action_bridge.py" \
 "$AGENTS/phase27_controller.py" \
 "$CTL/connectorregistryctl" "$CTL/liveexecutionctl" "$CTL/financialexecutionctl" \
 "$CTL/externalactionctl" "$CTL/phase27ctl" \
 "$CONN/financial_adapter.py" "$CONN/communications_adapter.py" \
 "$CONN/publication_adapter.py" "$CONN/deployment_adapter.py"

echo "[2/6] Registering connector slots..."
python "$CTL/connectorregistryctl" register financial primary-financial
python "$CTL/connectorregistryctl" register communications primary-communications
python "$CTL/connectorregistryctl" register publication primary-publication
python "$CTL/connectorregistryctl" register deployment primary-deployment

echo "[3/6] Authority checks..."
python "$CTL/financialauthorityctl" evaluate 1000 demo-source demo-destination USD test
python "$CTL/financialauthorityctl" evaluate 16000 demo-source demo-destination USD approval-test

echo "[4/6] Router health..."
python "$CTL/liveexecutionctl" status
python "$CTL/phase27ctl"

echo "[5/6] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text());jobs=d.setdefault("jobs",[])
job={"id":"phase27-execution-connectors","enabled":True,"interval_seconds":3600,
     "command":["python","companyos/phase27ctl"]}
e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:e.clear();e.update(job)
else:jobs.append(job)
p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY
python "$CTL/operationsctl" restart

echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos";errors=[]
req=[
r/"agents"/"connector_registry_engine.py",r/"agents"/"live_execution_router.py",
r/"agents"/"financial_execution_bridge.py",r/"agents"/"external_action_bridge.py",
r/"agents"/"phase27_controller.py",r/"companyos"/"connectorregistryctl",
r/"companyos"/"liveexecutionctl",r/"companyos"/"financialexecutionctl",
r/"companyos"/"externalactionctl",r/"companyos"/"phase27ctl",
r/"connectors"/"financial_adapter.py",r/"connectors"/"communications_adapter.py",
r/"connectors"/"publication_adapter.py",r/"connectors"/"deployment_adapter.py",
r/"ceo_memory"/"phase27_execution_config.json",r/"ceo_memory"/"connector_registry.json"
]
for p in req:
    if not p.exists() or p.stat().st_size<=0:errors.append(f"Missing/empty: {p}")
for p in req[:14]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))
cfg=json.loads((r/"ceo_memory"/"phase27_execution_config.json").read_text())
if cfg["financial"]["daily_total_limit_usd"]!=20000:errors.append("daily limit mismatch")
if cfg["financial"]["single_transaction_auto_approval_limit_usd"]!=15000:errors.append("single transaction limit mismatch")
reg=json.loads((r/"ceo_memory"/"connector_registry.json").read_text())
if len(reg.get("connectors",[]))<4:errors.append("connector slots missing")
print("--------------------------------------------")
print("PHASE 27 EXECUTION CONNECTOR CORE VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 27 LIVE EXECUTION CONNECTOR CORE INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Connector slots created for:"
echo "  - Financial execution"
echo "  - Communications"
echo "  - Public publication"
echo "  - Production deployment"
echo
echo "IMPORTANT:"
echo "  Connectors are fail-closed until you configure a specific provider,"
echo "  credential environment variable, target/account, and adapter."
echo "  No money, messages, posts, or deployments are sent by installation."
echo
echo "Commands:"
echo "  python companyos/connectorregistryctl list"
echo "  python companyos/liveexecutionctl status"
echo "  python companyos/financialexecutionctl status"
echo "  python companyos/phase27ctl"
