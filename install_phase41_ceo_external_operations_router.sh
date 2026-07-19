#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " PHASE 41 - CEO EXTERNAL OPERATIONS ROUTER"
echo "============================================================"

cat > "$MEM/phase41_external_operations_config.json" <<'JSON'
{
  "enabled": true,
  "mode": "autonomous_external_operations",
  "max_actions_per_cycle": 10,
  "stop_on_first_failure": false,
  "routes": {
    "treasury_transfer": {
      "enabled": true,
      "handler": "phase40",
      "owner_approval_required": false
    },
    "business_email": {
      "enabled": true,
      "handler": "communications",
      "owner_approval_required": false
    },
    "customer_message": {
      "enabled": true,
      "handler": "communications",
      "owner_approval_required": false
    },
    "public_publish": {
      "enabled": true,
      "handler": "publication",
      "owner_approval_required": false
    },
    "deploy_existing_approved_target": {
      "enabled": true,
      "handler": "deployment",
      "owner_approval_required": false
    },
    "contractual_commitment": {
      "enabled": true,
      "handler": "approval_queue",
      "owner_approval_required": true
    },
    "mass_outreach": {
      "enabled": true,
      "handler": "approval_queue",
      "owner_approval_required": true
    },
    "paid_ad_campaign": {
      "enabled": true,
      "handler": "approval_queue",
      "owner_approval_required": true
    },
    "new_production_target": {
      "enabled": true,
      "handler": "approval_queue",
      "owner_approval_required": true
    }
  }
}
JSON

cat > "$MEM/ceo_external_action_queue.json" <<'JSON'
{
  "actions": []
}
JSON

cat > "$MEM/phase41_idempotency.json" <<'JSON'
{
  "processed_action_ids": []
}
JSON

cat > "$MEM/phase41_state.json" <<'JSON'
{
  "last_run_at": null,
  "processed_count": 0,
  "failure_count": 0,
  "last_results": []
}
JSON

cat > "$AGENTS/phase41_action_submitter.py" <<'PY'
#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
P=ROOT/"ceo_memory"/"ceo_external_action_queue.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load():
    try:return json.loads(P.read_text())
    except:return {"actions":[]}
def save(d):P.write_text(json.dumps(d,indent=2))

if len(sys.argv)<4 or sys.argv[1]!="submit":
    print(json.dumps({
      "success":False,
      "status":"usage",
      "usage":"submit ACTION_TYPE JSON_PAYLOAD"
    },indent=2))
    raise SystemExit(1)

action_type=sys.argv[2]
payload=json.loads(sys.argv[3])
action_id=hashlib.sha256(
    f"{now()}|{action_type}|{json.dumps(payload,sort_keys=True)}".encode()
).hexdigest()[:24]

row={
  "action_id":action_id,
  "created_at":now(),
  "source":"ceo",
  "action_type":action_type,
  "payload":payload,
  "status":"pending"
}

d=load()
d.setdefault("actions",[]).append(row)
d["updated_at"]=now()
save(d)

print(json.dumps({
  "success":True,
  "status":"phase41_action_queued",
  "action":row
},indent=2))
PY
chmod +x "$AGENTS/phase41_action_submitter.py"

cat > "$CTL/phase41actionctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call(
    [sys.executable,str(r/"agents"/"phase41_action_submitter.py"),*sys.argv[1:]],
    cwd=r
))
PY
chmod +x "$CTL/phase41actionctl"

cat > "$AGENTS/phase41_external_operations_router.py" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys,shlex
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"phase41_external_operations_config.json"
QUEUE=MEM/"ceo_external_action_queue.json"
IDEM=MEM/"phase41_idempotency.json"
STATE=MEM/"phase41_state.json"
REPORT=MEM/"phase41_report.json"
AUDIT=MEM/"phase41_audit.jsonl"

def now(): return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

def audit(x):
    with AUDIT.open("a") as f:
        f.write(json.dumps({"at":now(),**x})+"\n")

def run(args,timeout=300):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=timeout)
    try:r=json.loads(p.stdout)
    except:r={"success":False,"status":"invalid_json_output","stdout":p.stdout[-3000:],"stderr":p.stderr[-1000:]}
    return p.returncode,r

def existing_ctl(*names):
    for n in names:
        p=ROOT/"companyos"/n
        if p.exists():
            return str(p)
    return None

def route_treasury(action):
    p=action["payload"]
    required=["chain","asset","destination","amount_native","amount_usd","reason"]
    missing=[k for k in required if p.get(k) in (None,"")]
    if missing:
        return {"success":False,"status":"missing_treasury_fields","missing":missing}

    return run([
      sys.executable,"companyos/phase40decisionctl","submit",
      str(p["chain"]),str(p["asset"]),str(p["destination"]),
      str(p["amount_native"]),str(p["amount_usd"]),str(p["reason"])
    ])[1]

def route_communications(action):
    ctl=existing_ctl("communicationsctl","communicationctl")
    if not ctl:
        return {"success":False,"status":"communications_controller_not_found"}

    p=action["payload"]
    # Generic connector handoff. Existing communications layer decides connector specifics.
    rc,r=run([sys.executable,ctl,"enqueue",json.dumps({
      "action_type":action["action_type"],
      "payload":p,
      "source":"phase41"
    })])
    return r if rc==0 else r

def route_publication(action):
    ctl=existing_ctl("publicationctl","publishctl")
    if not ctl:
        return {"success":False,"status":"publication_controller_not_found"}

    rc,r=run([sys.executable,ctl,"enqueue",json.dumps({
      "action_type":action["action_type"],
      "payload":action["payload"],
      "source":"phase41"
    })])
    return r if rc==0 else r

def route_deployment(action):
    ctl=existing_ctl("deploymentctl","deployctl")
    if not ctl:
        return {"success":False,"status":"deployment_controller_not_found"}

    rc,r=run([sys.executable,ctl,"enqueue",json.dumps({
      "action_type":action["action_type"],
      "payload":action["payload"],
      "source":"phase41"
    })],timeout=600)
    return r if rc==0 else r

def route_approval(action):
    p=MEM/"owner_approval_queue.json"
    d=load(p,{"items":[]})
    item={
      "approval_id":action["action_id"],
      "created_at":now(),
      "source":"phase41",
      "action_type":action["action_type"],
      "payload":action["payload"],
      "status":"pending_owner_approval"
    }
    d.setdefault("items",[]).append(item)
    save(p,d)
    return {
      "success":True,
      "status":"queued_for_owner_approval",
      "approval_id":action["action_id"]
    }

def dispatch(action,cfg):
    spec=(cfg.get("routes") or {}).get(action.get("action_type"))
    if not spec or not spec.get("enabled"):
        return {"success":False,"status":"action_type_not_enabled"}

    if spec.get("owner_approval_required"):
        return route_approval(action)

    handler=spec.get("handler")
    if handler=="phase40": return route_treasury(action)
    if handler=="communications": return route_communications(action)
    if handler=="publication": return route_publication(action)
    if handler=="deployment": return route_deployment(action)
    if handler=="approval_queue": return route_approval(action)

    return {"success":False,"status":"unknown_handler"}

def cycle():
    cfg=load(CFG,{})
    if not cfg.get("enabled"):
        return {"success":True,"status":"phase41_disabled"}

    q=load(QUEUE,{"actions":[]})
    idem=load(IDEM,{"processed_action_ids":[]})
    processed=set(idem.get("processed_action_ids",[]))
    pending=[x for x in q.get("actions",[]) if x.get("status","pending")=="pending"]

    results=[]
    failures=0

    for action in pending[:int(cfg.get("max_actions_per_cycle",10))]:
        aid=action.get("action_id")

        if aid in processed:
            action["status"]="duplicate_skipped"
            results.append({"action_id":aid,"success":True,"status":"duplicate_skipped"})
            continue

        r=dispatch(action,cfg)
        row={"action_id":aid,"action_type":action.get("action_type"),**r}
        results.append(row)
        audit(row)

        if r.get("success"):
            action["status"]="dispatched"
            action["dispatched_at"]=now()
            action["dispatch_result"]=r
            processed.add(aid)
        else:
            action["status"]="dispatch_failed"
            action["dispatch_result"]=r
            failures+=1
            if cfg.get("stop_on_first_failure"):
                break

    q["updated_at"]=now()
    save(QUEUE,q)
    save(IDEM,{"processed_action_ids":sorted(processed)})

    # Continue downstream governed financial pipeline.
    if any(x.get("success") and x.get("action_type")=="treasury_transfer" for x in results):
        run([sys.executable,"companyos/phase40ctl","run"],timeout=600)

    report={
      "generated_at":now(),
      "pending_count":len(pending),
      "processed_count":len(results),
      "failure_count":failures,
      "results":results
    }
    save(REPORT,report)
    save(STATE,{
      "last_run_at":now(),
      "processed_count":len(results),
      "failure_count":failures,
      "last_results":results[-10:]
    })

    return {
      "success":failures==0,
      "status":"phase41_external_operations_cycle_complete",
      "report":report
    }

a=sys.argv[1] if len(sys.argv)>1 else "run"

if a=="status":
    r={
      "success":True,
      "status":"phase41_external_operations_status",
      "config":load(CFG,{}),
      "state":load(STATE,{}),
      "idempotency":load(IDEM,{"processed_action_ids":[]}),
      "queue":load(QUEUE,{"actions":[]})
    }
else:
    r=cycle()

print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY
chmod +x "$AGENTS/phase41_external_operations_router.py"

cat > "$CTL/phase41ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call(
    [sys.executable,str(r/"agents"/"phase41_external_operations_router.py"),*sys.argv[1:]],
    cwd=r
))
PY
chmod +x "$CTL/phase41ctl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/phase41_action_submitter.py" \
  "$AGENTS/phase41_external_operations_router.py" \
  "$CTL/phase41actionctl" \
  "$CTL/phase41ctl"

echo "[2/5] Checking Phase 40..."
python "$CTL/phase40ctl" status >/dev/null
echo "Phase 40 available."

echo "[3/5] Status..."
python "$CTL/phase41ctl" status

echo "[4/5] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path

p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text())
jobs=d.setdefault("jobs",[])

job={
  "id":"phase41-external-operations-router",
  "enabled":True,
  "interval_seconds":60,
  "command":["python","companyos/phase41ctl","run"]
}

e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:
    e.clear();e.update(job)
else:
    jobs.append(job)

p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY

python "$CTL/operationsctl" restart

echo "[5/5] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path

r=Path.home()/"companyos"
errors=[]

req=[
  r/"agents"/"phase41_action_submitter.py",
  r/"agents"/"phase41_external_operations_router.py",
  r/"companyos"/"phase41actionctl",
  r/"companyos"/"phase41ctl",
  r/"ceo_memory"/"phase41_external_operations_config.json",
  r/"ceo_memory"/"ceo_external_action_queue.json",
  r/"ceo_memory"/"phase41_idempotency.json",
  r/"ceo_memory"/"phase41_state.json"
]

for p in req:
    if not p.exists() or p.stat().st_size<=0:
        errors.append(f"Missing/empty: {p}")

for p in req[:4]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))

cfg=json.loads((r/"ceo_memory"/"phase41_external_operations_config.json").read_text())

for key in ["treasury_transfer","business_email","customer_message","public_publish","deploy_existing_approved_target"]:
    if not cfg["routes"][key]["enabled"]:
        errors.append(f"{key} must be enabled")

if cfg["routes"]["treasury_transfer"]["owner_approval_required"]:
    errors.append("normal governed treasury transfers should not require per-transaction owner approval")
if cfg["routes"]["public_publish"]["owner_approval_required"]:
    errors.append("public publication should be autonomous under Phase41")
if cfg["routes"]["deploy_existing_approved_target"]["owner_approval_required"]:
    errors.append("approved target deployment should be autonomous under Phase41")

print("--------------------------------------------")
print("PHASE 41 EXTERNAL OPERATIONS ROUTER VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:
    print("ERROR:",e)
if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 41 CEO EXTERNAL OPERATIONS ROUTER INSTALLED"
echo " TREASURY TRANSFERS: CONNECTED TO GOVERNED PHASE 40 PIPELINE"
echo " BUSINESS COMMUNICATIONS: ROUTABLE"
echo " PUBLIC PUBLICATION: ROUTABLE"
echo " APPROVED-TARGET DEPLOYMENT: ROUTABLE"
echo " HIGH-COMMITMENT ACTIONS: OWNER APPROVAL QUEUE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/phase41ctl status"
echo "  python companyos/phase41ctl run"
echo '  python companyos/phase41actionctl submit public_publish '\''{"title":"Example","body":"Example content"}'\'''
