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
