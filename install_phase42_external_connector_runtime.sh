#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " PHASE 42 - EXTERNAL CONNECTOR RUNTIME + DELIVERY RECEIPTS"
echo "============================================================"

cat > "$MEM/phase42_connector_runtime_config.json" <<'JSON'
{
  "enabled": true,
  "fail_closed": true,
  "max_jobs_per_cycle": 10,
  "connectors": {
    "communications": {
      "enabled": true,
      "command_env": "COMPANYOS_COMMUNICATIONS_COMMAND"
    },
    "publication": {
      "enabled": true,
      "command_env": "COMPANYOS_PUBLICATION_COMMAND"
    },
    "deployment": {
      "enabled": true,
      "command_env": "COMPANYOS_DEPLOYMENT_COMMAND"
    }
  },
  "require_delivery_receipt": true,
  "require_idempotency": true,
  "never_log_secrets": true
}
JSON

cat > "$MEM/phase42_connector_queue.json" <<'JSON'
{
  "jobs": []
}
JSON

cat > "$MEM/phase42_delivery_receipts.json" <<'JSON'
{
  "receipts": []
}
JSON

cat > "$MEM/phase42_idempotency.json" <<'JSON'
{
  "processed_job_ids": []
}
JSON

cat > "$AGENTS/phase42_connector_runtime.py" <<'PY'
#!/usr/bin/env python3
import json, os, shlex, subprocess, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"phase42_connector_runtime_config.json"
QUEUE=MEM/"phase42_connector_queue.json"
RECEIPTS=MEM/"phase42_delivery_receipts.json"
IDEM=MEM/"phase42_idempotency.json"
STATE=MEM/"phase42_state.json"
AUDIT=MEM/"phase42_audit.jsonl"

def now(): return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

def audit(row):
    safe={k:v for k,v in row.items() if "key" not in k.lower() and "secret" not in k.lower()}
    with AUDIT.open("a") as f:
        f.write(json.dumps({"at":now(),**safe})+"\n")

def connector_spec(kind,cfg):
    return (cfg.get("connectors") or {}).get(kind)

def run_connector(kind,payload,cfg):
    spec=connector_spec(kind,cfg)
    if not spec or not spec.get("enabled"):
        return {"success":False,"status":"connector_disabled"}

    env_name=spec.get("command_env")
    command=os.getenv(env_name or "","").strip()
    if not command:
        return {
          "success":False,
          "status":"connector_command_not_configured",
          "connector":kind,
          "required_env":env_name
        }

    p=subprocess.run(
      shlex.split(command),
      input=json.dumps(payload),
      text=True,
      capture_output=True,
      timeout=600,
      env=os.environ.copy()
    )

    try:r=json.loads(p.stdout)
    except:
        r={
          "success":False,
          "status":"invalid_connector_output",
          "return_code":p.returncode,
          "stdout":p.stdout[-2000:],
          "stderr":p.stderr[-1000:]
        }

    if p.returncode!=0:
        r["success"]=False
    return r

def enqueue(kind,payload,source="phase41"):
    seed=f"{now()}|{kind}|{json.dumps(payload,sort_keys=True)}"
    jid=hashlib.sha256(seed.encode()).hexdigest()[:24]
    q=load(QUEUE,{"jobs":[]})
    row={
      "job_id":jid,
      "created_at":now(),
      "source":source,
      "connector":kind,
      "payload":payload,
      "status":"pending"
    }
    q.setdefault("jobs",[]).append(row)
    q["updated_at"]=now()
    save(QUEUE,q)
    return row

def cycle():
    cfg=load(CFG,{})
    if not cfg.get("enabled"):
        return {"success":True,"status":"phase42_disabled"}

    q=load(QUEUE,{"jobs":[]})
    idem=load(IDEM,{"processed_job_ids":[]})
    processed=set(idem.get("processed_job_ids",[]))
    receipts=load(RECEIPTS,{"receipts":[]})

    jobs=[j for j in q.get("jobs",[]) if j.get("status")=="pending"]
    results=[]
    failures=0

    for job in jobs[:int(cfg.get("max_jobs_per_cycle",10))]:
        jid=job["job_id"]

        if jid in processed:
            job["status"]="duplicate_skipped"
            results.append({"job_id":jid,"success":True,"status":"duplicate_skipped"})
            continue

        result=run_connector(job["connector"],job["payload"],cfg)

        receipt={
          "receipt_id":hashlib.sha256(f"{jid}|{now()}".encode()).hexdigest()[:24],
          "job_id":jid,
          "connector":job["connector"],
          "created_at":now(),
          "success":bool(result.get("success")),
          "status":result.get("status"),
          "external_reference":result.get("external_reference") or result.get("id") or result.get("txid"),
          "result":result
        }
        receipts.setdefault("receipts",[]).append(receipt)

        if result.get("success"):
            job["status"]="delivered"
            job["delivered_at"]=now()
            processed.add(jid)
        else:
            job["status"]="delivery_failed"
            failures+=1

        row={
          "job_id":jid,
          "connector":job["connector"],
          "success":bool(result.get("success")),
          "status":result.get("status")
        }
        results.append(row)
        audit(row)

    q["updated_at"]=now()
    save(QUEUE,q)
    save(RECEIPTS,receipts)
    save(IDEM,{"processed_job_ids":sorted(processed)})
    save(STATE,{
      "last_run_at":now(),
      "processed_count":len(results),
      "failure_count":failures,
      "last_results":results[-10:]
    })

    return {
      "success":failures==0,
      "status":"phase42_connector_cycle_complete",
      "results":results
    }

a=sys.argv[1] if len(sys.argv)>1 else "status"

if a=="enqueue":
    if len(sys.argv)<4:
        r={"success":False,"status":"usage","usage":"enqueue CONNECTOR JSON_PAYLOAD"}
    else:
        row=enqueue(sys.argv[2],json.loads(sys.argv[3]))
        r={"success":True,"status":"phase42_job_queued","job":row}

elif a=="run":
    r=cycle()

else:
    cfg=load(CFG,{})
    connector_status={}
    for name,spec in cfg.get("connectors",{}).items():
        env_name=spec.get("command_env")
        connector_status[name]={
          "enabled":spec.get("enabled"),
          "configured":bool(os.getenv(env_name or "","").strip()),
          "command_env":env_name
        }

    r={
      "success":True,
      "status":"phase42_connector_runtime_status",
      "connectors":connector_status,
      "queue":load(QUEUE,{"jobs":[]}),
      "state":load(STATE,{})
    }

print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/phase42_connector_runtime.py"

cat > "$CTL/phase42ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call(
    [sys.executable,str(r/"agents"/"phase42_connector_runtime.py"),*sys.argv[1:]],
    cwd=r
))
PY
chmod +x "$CTL/phase42ctl"

echo "[1/6] Installing Phase 41 connector shims..."

cat > "$CTL/communicationsctl" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
if len(sys.argv)>=3 and sys.argv[1]=="enqueue":
    wrapper=json.loads(sys.argv[2])
    payload=wrapper.get("payload",wrapper)
    raise SystemExit(subprocess.call(
      [sys.executable,"companyos/phase42ctl","enqueue","communications",json.dumps(payload)],
      cwd=r
    ))
print(json.dumps({"success":True,"status":"communications_connector_shim_ready"},indent=2))
PY

cat > "$CTL/publicationctl" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
if len(sys.argv)>=3 and sys.argv[1]=="enqueue":
    wrapper=json.loads(sys.argv[2])
    payload=wrapper.get("payload",wrapper)
    raise SystemExit(subprocess.call(
      [sys.executable,"companyos/phase42ctl","enqueue","publication",json.dumps(payload)],
      cwd=r
    ))
print(json.dumps({"success":True,"status":"publication_connector_shim_ready"},indent=2))
PY

cat > "$CTL/deploymentctl" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
if len(sys.argv)>=3 and sys.argv[1]=="enqueue":
    wrapper=json.loads(sys.argv[2])
    payload=wrapper.get("payload",wrapper)
    raise SystemExit(subprocess.call(
      [sys.executable,"companyos/phase42ctl","enqueue","deployment",json.dumps(payload)],
      cwd=r
    ))
print(json.dumps({"success":True,"status":"deployment_connector_shim_ready"},indent=2))
PY

chmod +x "$CTL/communicationsctl" "$CTL/publicationctl" "$CTL/deploymentctl"

echo "[2/6] Compiling..."
python -m py_compile \
  "$AGENTS/phase42_connector_runtime.py" \
  "$CTL/phase42ctl" \
  "$CTL/communicationsctl" \
  "$CTL/publicationctl" \
  "$CTL/deploymentctl"

echo "[3/6] Status..."
python "$CTL/phase42ctl" status

echo "[4/6] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text())
jobs=d.setdefault("jobs",[])
job={
  "id":"phase42-external-connector-runtime",
  "enabled":True,
  "interval_seconds":60,
  "command":["python","companyos/phase42ctl","run"]
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

echo "[5/6] Writing secure connector setup template..."
cat > "$HOME/.companyos_secure/phase42_connector_setup.txt" <<'TXT'
Optional external connector commands go in ~/.companyos_secrets:

export COMPANYOS_COMMUNICATIONS_COMMAND='YOUR_LOCAL_COMMUNICATION_CONNECTOR_COMMAND'
export COMPANYOS_PUBLICATION_COMMAND='YOUR_LOCAL_PUBLICATION_CONNECTOR_COMMAND'
export COMPANYOS_DEPLOYMENT_COMMAND='YOUR_LOCAL_DEPLOYMENT_CONNECTOR_COMMAND'

Each connector must:
1. Read one JSON payload from stdin.
2. Perform the configured external action.
3. Return JSON on stdout:
   {"success":true,"status":"delivered","external_reference":"..."}
4. Exit nonzero on failure.

Do not place API keys directly in repository files.
TXT

echo "[6/6] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path
r=Path.home()/"companyos"
errors=[]

req=[
 r/"agents"/"phase42_connector_runtime.py",
 r/"companyos"/"phase42ctl",
 r/"companyos"/"communicationsctl",
 r/"companyos"/"publicationctl",
 r/"companyos"/"deploymentctl",
 r/"ceo_memory"/"phase42_connector_runtime_config.json",
 r/"ceo_memory"/"phase42_connector_queue.json",
 r/"ceo_memory"/"phase42_delivery_receipts.json",
 r/"ceo_memory"/"phase42_idempotency.json"
]

for p in req:
    if not p.exists() or p.stat().st_size<=0:
        errors.append(f"Missing/empty: {p}")

cfg=json.loads((r/"ceo_memory"/"phase42_connector_runtime_config.json").read_text())
if not cfg.get("fail_closed"):
    errors.append("connector runtime must fail closed")
if not cfg.get("require_delivery_receipt"):
    errors.append("delivery receipts must be required")
if not cfg.get("require_idempotency"):
    errors.append("idempotency must be required")

print("--------------------------------------------")
print("PHASE 42 CONNECTOR RUNTIME VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors: print("ERROR:",e)
if errors: raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 42 EXTERNAL CONNECTOR RUNTIME INSTALLED"
echo " COMMUNICATION / PUBLICATION / DEPLOYMENT SHIMS: CONNECTED"
echo " DELIVERY RECEIPTS: ENABLED"
echo " IDEMPOTENCY: ENABLED"
echo " UNCONFIGURED CONNECTORS: FAIL-CLOSED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/phase42ctl status"
echo "  python companyos/phase42ctl run"
echo
echo "Next: configure real connector commands locally in ~/.companyos_secrets."
