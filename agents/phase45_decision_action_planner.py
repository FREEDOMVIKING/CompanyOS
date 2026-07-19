#!/usr/bin/env python3
import json, subprocess, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"phase45_decision_planner_config.json"
P44Q=MEM/"phase44_opportunity_queue.json"
P44O=MEM/"phase44_revenue_outcomes.json"
PLANS=MEM/"phase45_plan_queue.json"
STATE=MEM/"phase45_state.json"
IDEM=MEM/"phase45_idempotency.json"
REPORT=MEM/"phase45_report.json"
AUDIT=MEM/"phase45_audit.jsonl"

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

def plan_id(oid):
    return hashlib.sha256(f"phase45|{oid}".encode()).hexdigest()[:24]

def step_id(pid,index,action_type,payload):
    seed=f"{pid}|{index}|{action_type}|{json.dumps(payload,sort_keys=True)}"
    return hashlib.sha256(seed.encode()).hexdigest()[:24]

def build_plan(o,cfg):
    action=o.get("recommended_action_type")
    payload=o.get("recommended_action_payload") or {}
    pid=plan_id(o["opportunity_id"])

    steps=[]

    # Step 1: validate opportunity before any external action.
    steps.append({
      "step_index":1,
      "action_type":"internal_validate_opportunity",
      "payload":{
        "opportunity_id":o["opportunity_id"],
        "priority_score":o.get("priority_score"),
        "expected_value_usd":o.get("expected_value_usd")
      },
      "status":"pending"
    })

    # Step 2: primary external action recommended by Phase 44.
    if action:
        steps.append({
          "step_index":2,
          "action_type":action,
          "payload":payload,
          "status":"pending"
        })

    # Step 3: result validation checkpoint.
    steps.append({
      "step_index":len(steps)+1,
      "action_type":"internal_validate_result",
      "payload":{
        "opportunity_id":o["opportunity_id"]
      },
      "status":"pending"
    })

    for s in steps:
        s["step_id"]=step_id(pid,s["step_index"],s["action_type"],s["payload"])

    return {
      "plan_id":pid,
      "opportunity_id":o["opportunity_id"],
      "title":o.get("title"),
      "priority_score":o.get("priority_score"),
      "expected_value_usd":o.get("expected_value_usd"),
      "status":"ready",
      "created_at":now(),
      "steps":steps[:int(cfg.get("max_steps_per_plan",8))]
    }

def create_plans(cfg,idem):
    q=load(P44Q,{"opportunities":[]})
    plans=load(PLANS,{"plans":[]})
    planned=set(idem.get("planned_opportunity_ids",[]))
    created=[]

    candidates=[
      o for o in q.get("opportunities",[])
      if float(o.get("priority_score",0) or 0) >= float(cfg.get("minimum_priority_score",55))
      and o.get("status") in ("dispatched","ready","scored","new")
    ]

    for o in candidates[:int(cfg.get("max_opportunities_per_cycle",5))]:
        oid=o.get("opportunity_id")
        if not oid or oid in planned:
            continue

        p=build_plan(o,cfg)
        plans.setdefault("plans",[]).append(p)
        planned.add(oid)
        created.append(p["plan_id"])

    plans["updated_at"]=now()
    save(PLANS,plans)
    idem["planned_opportunity_ids"]=sorted(planned)
    save(IDEM,idem)
    return created

def dispatch_step(plan,step,cfg,idem):
    sid=step["step_id"]
    dispatched=set(idem.get("dispatched_step_ids",[]))

    if sid in dispatched:
        return {"success":True,"status":"duplicate_step_skipped"}

    at=step["action_type"]

    if at=="internal_validate_opportunity":
        ok=float(plan.get("priority_score",0) or 0) >= float(cfg.get("minimum_priority_score",55))
        step["status"]="completed" if ok else "blocked"
        return {
          "success":ok,
          "status":"opportunity_validation_passed" if ok else "opportunity_validation_failed"
        }

    if at=="internal_validate_result":
        # Outcome validation remains internal and non-destructive.
        outcomes=load(P44O,{"outcomes":[]}).get("outcomes",[])
        step["status"]="completed"
        return {
          "success":True,
          "status":"result_validation_recorded",
          "known_outcomes":len(outcomes)
        }

    if at in cfg.get("approval_gated_action_types",[]):
        step["status"]="blocked"
        return {"success":False,"status":"owner_approval_required"}

    if at not in cfg.get("allowed_action_types",[]):
        step["status"]="blocked"
        return {"success":False,"status":"action_type_not_allowed"}

    rc,r=run([
      sys.executable,
      "companyos/phase41actionctl",
      "submit",
      at,
      json.dumps(step.get("payload") or {})
    ])

    if rc==0 and r.get("success"):
        step["status"]="dispatched"
        step["phase41_action_id"]=(r.get("action") or {}).get("action_id")
        dispatched.add(sid)
        idem["dispatched_step_ids"]=sorted(dispatched)
        save(IDEM,idem)
        return {
          "success":True,
          "status":"external_step_dispatched",
          "phase41_action_id":step.get("phase41_action_id")
        }

    step["status"]="dispatch_failed"
    return {"success":False,"status":"external_step_dispatch_failed","detail":r}

def execute_plans(cfg,idem):
    data=load(PLANS,{"plans":[]})
    results=[]
    dispatched=0
    blocked=0
    completed=0

    for plan in data.get("plans",[]):
        if plan.get("status") not in ("ready","in_progress"):
            continue

        plan["status"]="in_progress"

        for step in plan.get("steps",[]):
            if step.get("status") in ("completed","dispatched"):
                continue

            r=dispatch_step(plan,step,cfg,idem)
            row={
              "plan_id":plan["plan_id"],
              "step_id":step["step_id"],
              "action_type":step["action_type"],
              **r
            }
            results.append(row)
            audit(row)

            if r.get("status")=="external_step_dispatched":
                dispatched+=1
                break

            if not r.get("success"):
                blocked+=1
                plan["status"]="blocked"
                plan["blocked_at"]=now()
                break

        if all(s.get("status") in ("completed","dispatched") for s in plan.get("steps",[])):
            plan["status"]="completed"
            plan["completed_at"]=now()
            completed+=1

    data["updated_at"]=now()
    save(PLANS,data)
    return results,dispatched,blocked,completed

def cycle():
    cfg=load(CFG,{})
    if not cfg.get("enabled"):
        return {"success":True,"status":"phase45_disabled"}

    idem=load(IDEM,{"planned_opportunity_ids":[],"dispatched_step_ids":[]})

    created=create_plans(cfg,idem)
    results,dispatched,blocked,completed=execute_plans(cfg,idem)

    # Continue routed external work and feedback loop.
    rc43,r43=run([sys.executable,"companyos/phase43ctl","run"])

    state={
      "last_run_at":now(),
      "created_plans":len(created),
      "dispatched_steps":dispatched,
      "blocked_steps":blocked,
      "completed_plans":completed,
      "last_results":results[-20:]
    }
    save(STATE,state)

    report={
      "generated_at":now(),
      "created_plan_ids":created,
      "dispatched_steps":dispatched,
      "blocked_steps":blocked,
      "completed_plans":completed,
      "phase43":{"return_code":rc43,"result":r43},
      "results":results
    }
    save(REPORT,report)

    return {
      "success":rc43==0 and bool(r43.get("success")),
      "status":"phase45_decision_action_cycle_complete",
      "report":report
    }

a=sys.argv[1] if len(sys.argv)>1 else "run"

if a=="status":
    r={
      "success":True,
      "status":"phase45_decision_action_status",
      "config":load(CFG,{}),
      "state":load(STATE,{}),
      "plans":load(PLANS,{"plans":[]}),
      "idempotency":load(IDEM,{"planned_opportunity_ids":[],"dispatched_step_ids":[]})
    }
else:
    r=cycle()

print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
