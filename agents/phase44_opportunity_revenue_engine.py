#!/usr/bin/env python3
import json, subprocess, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"phase44_opportunity_revenue_config.json"
QUEUE=MEM/"phase44_opportunity_queue.json"
OUTCOMES=MEM/"phase44_revenue_outcomes.json"
STATE=MEM/"phase44_state.json"
IDEM=MEM/"phase44_idempotency.json"

P17=MEM/"opportunity_discovery_results.json"
P43=MEM/"phase43_learning_feed.json"
P41Q=MEM/"ceo_external_action_queue.json"

REPORT=MEM/"phase44_report.json"
AUDIT=MEM/"phase44_audit.jsonl"

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

def run(args,timeout=600):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=timeout)
    try:r=json.loads(p.stdout)
    except:r={"success":False,"status":"invalid_json_output","stdout":p.stdout[-3000:],"stderr":p.stderr[-1000:]}
    return p.returncode,r

def clamp(v,a=0,b=100):
    try:return max(a,min(b,float(v)))
    except:return 0.0

def score(o,cfg):
    w=cfg["scoring_weights"]
    ev=clamp(o.get("expected_value_score",0))
    ps=clamp(o.get("probability_score",0))
    ur=clamp(o.get("urgency_score",0))
    sf=clamp(o.get("strategic_fit_score",0))
    er=clamp(o.get("execution_readiness_score",0))
    rp=clamp(o.get("risk_score",0))
    total=(
      ev*w["expected_value"]+
      ps*w["probability_of_success"]+
      ur*w["urgency"]+
      sf*w["strategic_fit"]+
      er*w["execution_readiness"]-
      rp*w["risk_penalty"]
    )
    return round(max(0,min(100,total)),2)

def normalize_opportunity(o):
    # Phase 17 may return plain strings as discovery results.
    # Normalize them into opportunity dictionaries before processing.
    if isinstance(o, str):
        o = {
            "title": o,
            "description": o,
            "source": "phase17",
            "evidence": [o]
        }
    elif not isinstance(o, dict):
        o = {
            "title": str(o),
            "description": str(o),
            "source": "phase17",
            "evidence": [str(o)]
        }

    oid=o.get("opportunity_id")
    if not oid:
        seed=json.dumps(o,sort_keys=True)
        oid=hashlib.sha256(seed.encode()).hexdigest()[:24]
    return {
      "opportunity_id":oid,
      "title":o.get("title") or o.get("name") or "Untitled opportunity",
      "description":o.get("description") or o.get("summary") or "",
      "source":o.get("source","internal"),
      "expected_value_usd":float(o.get("expected_value_usd",0) or 0),
      "expected_value_score":o.get("expected_value_score",o.get("value_score",50)),
      "probability_score":o.get("probability_score",o.get("confidence",50)),
      "urgency_score":o.get("urgency_score",50),
      "strategic_fit_score":o.get("strategic_fit_score",50),
      "execution_readiness_score":o.get("execution_readiness_score",50),
      "risk_score":o.get("risk_score",25),
      "recommended_action_type":o.get("recommended_action_type") or o.get("action_type"),
      "recommended_action_payload":o.get("recommended_action_payload") or o.get("payload") or {},
      "evidence":o.get("evidence") or o.get("findings") or [],
      "status":o.get("status","new"),
      "created_at":o.get("created_at",now())
    }

def ingest_discovery():
    q=load(QUEUE,{"opportunities":[]})
    existing={x.get("opportunity_id") for x in q.get("opportunities",[])}

    src=load(P17,{})
    rows=src.get("opportunities") or src.get("results") or []

    added=0
    for raw in rows:
        o=normalize_opportunity(raw)
        if o["opportunity_id"] in existing:
            continue
        q.setdefault("opportunities",[]).append(o)
        existing.add(o["opportunity_id"])
        added+=1

    q["updated_at"]=now()
    save(QUEUE,q)
    return added

def action_allowed(o,cfg):
    action=o.get("recommended_action_type")
    if not action:
        return False,"missing_action_type"
    if action in cfg.get("blocked_without_owner_approval",[]):
        return False,"owner_approval_required"
    if action not in cfg.get("allowed_action_types",[]):
        return False,"action_type_not_allowed"
    if cfg.get("require_evidence") and not o.get("evidence"):
        return False,"evidence_required"
    if o.get("expected_value_usd",0) < float(cfg.get("minimum_expected_value_usd",0)):
        return False,"expected_value_below_minimum"
    return True,None

def dispatch(o):
    action_type=o["recommended_action_type"]
    payload=o.get("recommended_action_payload") or {}

    rc,r=run([
      sys.executable,
      "companyos/phase41actionctl",
      "submit",
      action_type,
      json.dumps(payload)
    ])
    return rc,r

def learn_from_phase43(outcomes):
    feed=load(P43,{"events":[]})
    existing={x.get("event_id") for x in outcomes.get("outcomes",[])}

    added=0
    for e in feed.get("events",[]):
        eid=e.get("event_id")
        if not eid or eid in existing:
            continue

        outcomes.setdefault("outcomes",[]).append({
          "event_id":eid,
          "captured_at":now(),
          "source":"phase43",
          "success":bool(e.get("success")),
          "status":e.get("status"),
          "connector":e.get("connector"),
          "external_reference":e.get("external_reference"),
          "learning_type":e.get("learning_type")
        })
        existing.add(eid)
        added+=1
    return added

def cycle():
    cfg=load(CFG,{})
    if not cfg.get("enabled"):
        return {"success":True,"status":"phase44_disabled"}

    discovered=ingest_discovery()
    q=load(QUEUE,{"opportunities":[]})
    idem=load(IDEM,{"processed_opportunity_ids":[]})
    processed=set(idem.get("processed_opportunity_ids",[]))
    outcomes=load(OUTCOMES,{"outcomes":[]})

    results=[]
    dispatched=0
    blocked=0

    candidates=[
      o for o in q.get("opportunities",[])
      if o.get("status") in ("new","scored","ready")
    ]

    for o in candidates[:int(cfg.get("max_opportunities_per_cycle",10))]:
        oid=o["opportunity_id"]

        if oid in processed:
            o["status"]="duplicate_skipped"
            results.append({"opportunity_id":oid,"success":True,"status":"duplicate_skipped"})
            continue

        o["priority_score"]=score(o,cfg)

        if o["priority_score"] < float(cfg.get("minimum_priority_score",55)):
            o["status"]="below_priority_threshold"
            blocked+=1
            row={
              "opportunity_id":oid,
              "success":True,
              "status":"below_priority_threshold",
              "priority_score":o["priority_score"]
            }
            results.append(row)
            audit(row)
            processed.add(oid)
            continue

        allowed,reason=action_allowed(o,cfg)
        if not allowed:
            o["status"]="blocked"
            o["block_reason"]=reason
            blocked+=1
            row={
              "opportunity_id":oid,
              "success":False,
              "status":"opportunity_blocked",
              "reason":reason,
              "priority_score":o["priority_score"]
            }
            results.append(row)
            audit(row)
            processed.add(oid)
            continue

        rc,r=dispatch(o)

        if rc==0 and r.get("success"):
            o["status"]="dispatched"
            o["dispatched_at"]=now()
            o["phase41_action_id"]=(r.get("action") or {}).get("action_id")
            dispatched+=1
            row={
              "opportunity_id":oid,
              "success":True,
              "status":"opportunity_dispatched",
              "priority_score":o["priority_score"],
              "phase41_action_id":o.get("phase41_action_id")
            }
        else:
            o["status"]="dispatch_failed"
            o["dispatch_result"]=r
            blocked+=1
            row={
              "opportunity_id":oid,
              "success":False,
              "status":"opportunity_dispatch_failed",
              "detail":r
            }

        results.append(row)
        audit(row)
        processed.add(oid)

    q["updated_at"]=now()
    save(QUEUE,q)
    save(IDEM,{"processed_opportunity_ids":sorted(processed)})

    # Let Phase43 continue the routed work and collect feedback.
    rc43,r43=run([sys.executable,"companyos/phase43ctl","run"])

    outcome_added=learn_from_phase43(outcomes)
    outcomes["updated_at"]=now()
    save(OUTCOMES,outcomes)

    state={
      "last_run_at":now(),
      "discovered_count":discovered,
      "dispatched_count":dispatched,
      "blocked_count":blocked,
      "outcome_count":len(outcomes.get("outcomes",[])),
      "last_results":results[-20:]
    }
    save(STATE,state)

    report={
      "generated_at":now(),
      "discovered_count":discovered,
      "candidate_count":len(candidates),
      "dispatched_count":dispatched,
      "blocked_count":blocked,
      "outcome_events_added":outcome_added,
      "phase43":{"return_code":rc43,"result":r43},
      "results":results
    }
    save(REPORT,report)

    return {
      "success":rc43==0 and bool(r43.get("success")),
      "status":"phase44_opportunity_revenue_cycle_complete",
      "report":report
    }

a=sys.argv[1] if len(sys.argv)>1 else "run"

if a=="status":
    r={
      "success":True,
      "status":"phase44_opportunity_revenue_status",
      "config":load(CFG,{}),
      "state":load(STATE,{}),
      "queue":load(QUEUE,{"opportunities":[]}),
      "outcomes":load(OUTCOMES,{"outcomes":[]})
    }
else:
    r=cycle()

print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
