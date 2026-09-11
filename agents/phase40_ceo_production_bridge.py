#!/usr/bin/env python3
import json, subprocess, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"phase40_ceo_production_config.json"
DECISIONS=MEM/"ceo_production_decisions.json"
IDEM=MEM/"phase40_idempotency.json"
STATE=MEM/"phase40_state.json"
REPORT=MEM/"phase40_report.json"
AUDIT=MEM/"phase40_audit.jsonl"

def now():
    return datetime.now(timezone.utc).isoformat()

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

def run_cmd(args):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=300)
    try:r=json.loads(p.stdout)
    except:r={"success":False,"status":"invalid_json_output","stdout":p.stdout[-3000:],"stderr":p.stderr[-1000:]}
    return p.returncode,r

def normalize_decision_id(d):
    if d.get("decision_id"):
        return str(d["decision_id"])
    seed=json.dumps({
      "action_type":d.get("action_type"),
      "chain":d.get("chain"),
      "asset":d.get("asset"),
      "destination":d.get("destination"),
      "amount_native":d.get("amount_native"),
      "amount_usd":d.get("amount_usd"),
      "reason":d.get("reason")
    },sort_keys=True)
    return hashlib.sha256(seed.encode()).hexdigest()[:24]

def validate(d,cfg):
    reasons=[]
    if d.get("action_type")!="treasury_transfer":
        reasons.append("action_type_must_be_treasury_transfer")

    required=["chain","asset","destination","amount_native","amount_usd","reason"]
    for k in required:
        if d.get(k) in (None,""):
            reasons.append(f"missing_{k}")

    chain=d.get("chain")
    asset=d.get("asset")
    if asset not in cfg.get("allowed_production_routes",{}).get(chain,[]):
        reasons.append("route_not_enabled_for_phase40")

    try:
        usd=float(d.get("amount_usd",0))
        if usd<=0:
            reasons.append("amount_usd_must_be_positive")
        if usd>float(cfg["single_transaction_auto_limit_usd"]):
            reasons.append("single_transaction_limit_exceeded")
    except:
        reasons.append("invalid_amount_usd")

    try:
        native=float(d.get("amount_native",0))
        if native<=0:
            reasons.append("amount_native_must_be_positive")
    except:
        reasons.append("invalid_amount_native")

    return reasons

def enqueue_to_phase35(d):
    args=[
      sys.executable,
      "companyos/ceotreasuryrequestctl",
      "create",
      str(d["amount_usd"]),
      str(d["amount_native"]),
      d["asset"],
      d["chain"],
      d["destination"],
      d["reason"],
      str(d["decision_id"])
    ]
    return run_cmd(args)

def cycle():
    cfg=load(CFG,{})
    if not cfg.get("enabled"):
        return {"success":True,"status":"phase40_disabled"}

    q=load(DECISIONS,{"decisions":[]})
    idem=load(IDEM,{"processed_decision_ids":[]})
    processed=set(idem.get("processed_decision_ids",[]))

    pending=[
      d for d in q.get("decisions",[])
      if d.get("status","pending")=="pending"
    ]

    results=[]
    failures=0

    for d in pending[:int(cfg.get("max_decisions_per_cycle",5))]:
        d["decision_id"]=normalize_decision_id(d)

        if d["decision_id"] in processed:
            d["status"]="duplicate_skipped"
            row={
              "decision_id":d["decision_id"],
              "success":True,
              "status":"duplicate_skipped"
            }
            results.append(row)
            continue

        reasons=validate(d,cfg)
        if reasons:
            d["status"]="blocked"
            d["block_reasons"]=reasons
            row={
              "decision_id":d["decision_id"],
              "success":False,
              "status":"phase40_decision_blocked",
              "reasons":reasons
            }
            results.append(row)
            audit(row)
            failures+=1
            if cfg.get("stop_on_first_failure"):
                break
            continue

        rc,enq=enqueue_to_phase35(d)
        if rc!=0 or not enq.get("success"):
            d["status"]="enqueue_failed"
            row={
              "decision_id":d["decision_id"],
              "success":False,
              "status":"phase35_enqueue_failed",
              "detail":enq
            }
            results.append(row)
            audit(row)
            failures+=1
            if cfg.get("stop_on_first_failure"):
                break
            continue

        d["status"]="submitted_to_phase35"
        d["submitted_at"]=now()
        d["phase35_request"]=enq.get("request")

        processed.add(d["decision_id"])
        idem["processed_decision_ids"]=sorted(processed)
        save(IDEM,idem)

        row={
          "decision_id":d["decision_id"],
          "success":True,
          "status":"submitted_to_governed_production_pipeline",
          "phase35_request_id":(enq.get("request") or {}).get("request_id")
        }
        results.append(row)
        audit(row)

    q["updated_at"]=now()
    save(DECISIONS,q)

    # Run the existing governed pipeline only after successful submission.
    pipeline=None
    if any(x.get("success") and x.get("status")=="submitted_to_governed_production_pipeline" for x in results):
        rc35,r35=run_cmd([sys.executable,"companyos/ceotreasurybridgectl","run"])
        rc39,r39=run_cmd([sys.executable,"companyos/phase39ctl","run"])
        pipeline={
          "phase35":{"return_code":rc35,"result":r35},
          "phase39":{"return_code":rc39,"result":r39}
        }
        if rc35!=0 or rc39!=0 or not r35.get("success") or not r39.get("success"):
            failures+=1

    report={
      "generated_at":now(),
      "pending_count":len(pending),
      "processed_count":len(results),
      "failure_count":failures,
      "results":results,
      "pipeline":pipeline
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
      "status":"phase40_ceo_production_cycle_complete",
      "report":report
    }

a=sys.argv[1] if len(sys.argv)>1 else "run"

if a=="status":
    r={
      "success":True,
      "status":"phase40_ceo_production_status",
      "config":load(CFG,{}),
      "state":load(STATE,{}),
      "idempotency":load(IDEM,{"processed_decision_ids":[]}),
      "queue":load(DECISIONS,{"decisions":[]})
    }
else:
    r=cycle()

print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
