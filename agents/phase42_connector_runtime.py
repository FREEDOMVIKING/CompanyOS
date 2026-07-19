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
