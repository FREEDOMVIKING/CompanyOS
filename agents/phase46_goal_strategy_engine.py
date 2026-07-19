#!/usr/bin/env python3
import json, subprocess, sys, hashlib, math
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"phase46_goal_strategy_config.json"
GOALS=MEM/"company_goals.json"
STRATS=MEM/"phase46_strategy_registry.json"
STATE=MEM/"phase46_state.json"
LEARN=MEM/"phase46_learning_history.json"
P44Q=MEM/"phase44_opportunity_queue.json"
P44O=MEM/"phase44_revenue_outcomes.json"
P45=MEM/"phase45_plan_queue.json"
REPORT=MEM/"phase46_report.json"
AUDIT=MEM/"phase46_audit.jsonl"

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

def progress(goal):
    try:
        target=float(goal.get("target_value",0))
        current=float(goal.get("current_value",0))
        if target==0:return 0.0
        return round(max(0,min(100,(current/target)*100)),2)
    except:
        return 0.0

def make_strategy(goal,kind,index):
    sid=hashlib.sha256(f"{goal['goal_id']}|{kind}|{index}".encode()).hexdigest()[:24]

    templates={
      "acquire_customers":{
        "name":"Customer acquisition strategy",
        "hypothesis":"More qualified outreach and faster follow-up should increase conversion.",
        "recommended_action_type":"customer_message"
      },
      "increase_revenue":{
        "name":"Revenue expansion strategy",
        "hypothesis":"Prioritizing highest-value opportunities should increase revenue efficiency.",
        "recommended_action_type":"business_email"
      },
      "launch_offer":{
        "name":"Offer launch strategy",
        "hypothesis":"Publishing a focused offer should generate measurable demand.",
        "recommended_action_type":"public_publish"
      },
      "improve_operations":{
        "name":"Operational efficiency strategy",
        "hypothesis":"Reducing friction in existing workflows should improve throughput.",
        "recommended_action_type":"deploy_existing_approved_target"
      }
    }

    t=templates[kind]
    return {
      "strategy_id":sid,
      "goal_id":goal["goal_id"],
      "name":t["name"],
      "hypothesis":t["hypothesis"],
      "recommended_action_type":t["recommended_action_type"],
      "status":"candidate",
      "confidence":0.65,
      "created_at":now()
    }

def ensure_strategies(goal,cfg,registry):
    existing=[s for s in registry.get("strategies",[]) if s.get("goal_id")==goal["goal_id"]]
    if existing:
        return existing

    kinds=["acquire_customers","increase_revenue","launch_offer","improve_operations"]
    created=[]
    for i,k in enumerate(kinds[:int(cfg.get("max_strategies_per_goal",5))],1):
        s=make_strategy(goal,k,i)
        registry.setdefault("strategies",[]).append(s)
        created.append(s)
    return created

def strategy_score(s,goal,outcomes):
    base=float(s.get("confidence",0.5))*100
    p=progress(goal)

    related=[o for o in outcomes if o.get("strategy_id")==s.get("strategy_id")]
    success=sum(1 for x in related if x.get("success"))
    failed=sum(1 for x in related if x.get("success") is False)

    score=base + success*8 - failed*10 + min(10,p*0.1)
    return round(max(0,min(100,score)),2)

def generate_opportunity(goal,strategy):
    oid=hashlib.sha256(f"{goal['goal_id']}|{strategy['strategy_id']}|{now()}".encode()).hexdigest()[:24]

    title=f"{strategy['name']} for goal: {goal['title']}"
    description=f"Advance the goal '{goal['title']}' using strategy '{strategy['name']}'."

    payload={
      "goal_id":goal["goal_id"],
      "strategy_id":strategy["strategy_id"],
      "message":description
    }

    return {
      "opportunity_id":oid,
      "title":title,
      "description":description,
      "source":"phase46_goal_strategy_engine",
      "expected_value_usd":max(25,float(goal.get("priority",70))*10),
      "expected_value_score":min(100,float(goal.get("priority",70))+10),
      "probability_score":strategy.get("strategy_score",65),
      "urgency_score":float(goal.get("priority",70)),
      "strategic_fit_score":95,
      "execution_readiness_score":75,
      "risk_score":20,
      "recommended_action_type":strategy["recommended_action_type"],
      "recommended_action_payload":payload,
      "evidence":[
        f"Goal objective: {goal['objective']}",
        f"Current progress: {progress(goal)}%",
        f"Strategy hypothesis: {strategy['hypothesis']}"
      ],
      "goal_id":goal["goal_id"],
      "strategy_id":strategy["strategy_id"],
      "status":"new",
      "created_at":now()
    }

def ingest_feedback(registry,learning):
    outcomes=load(P44O,{"outcomes":[]}).get("outcomes",[])
    plans=load(P45,{"plans":[]}).get("plans",[])
    added=0
    seen={e.get("event_key") for e in learning.get("events",[])}

    for p in plans:
        key=f"plan:{p.get('plan_id')}:{p.get('status')}"
        if key in seen:continue
        learning.setdefault("events",[]).append({
          "event_key":key,
          "created_at":now(),
          "source":"phase45",
          "plan_id":p.get("plan_id"),
          "opportunity_id":p.get("opportunity_id"),
          "status":p.get("status")
        })
        seen.add(key);added+=1

    for o in outcomes:
        key=f"outcome:{o.get('event_id')}"
        if key in seen:continue
        learning.setdefault("events",[]).append({
          "event_key":key,
          "created_at":now(),
          "source":"phase44_outcome",
          "success":o.get("success"),
          "status":o.get("status"),
          "external_reference":o.get("external_reference")
        })
        seen.add(key);added+=1

    return added

def cycle():
    cfg=load(CFG,{})
    if not cfg.get("enabled"):
        return {"success":True,"status":"phase46_disabled"}

    goals=load(GOALS,{"goals":[]})
    registry=load(STRATS,{"strategies":[]})
    learning=load(LEARN,{"events":[]})
    p44q=load(P44Q,{"opportunities":[]})
    outcomes=load(P44O,{"outcomes":[]}).get("outcomes",[])

    feedback_added=ingest_feedback(registry,learning)

    generated=[]
    results=[]
    completed=0

    active=[g for g in goals.get("goals",[]) if g.get("status")=="active"]

    for goal in active[:int(cfg.get("max_active_goals",8))]:
        goal["progress_pct"]=progress(goal)

        if goal["progress_pct"]>=100:
            goal["status"]="completed"
            goal["completed_at"]=now()
            completed+=1
            continue

        strategies=ensure_strategies(goal,cfg,registry)

        for s in strategies:
            s["strategy_score"]=strategy_score(s,goal,outcomes)

        strategies.sort(key=lambda x:x.get("strategy_score",0),reverse=True)
        best=strategies[0] if strategies else None

        if not best:
            results.append({
              "goal_id":goal["goal_id"],
              "success":False,
              "status":"no_strategy_available"
            })
            continue

        best["status"]="selected"
        best["selected_at"]=now()

        existing_for_goal=[
          o for o in p44q.get("opportunities",[])
          if o.get("goal_id")==goal["goal_id"]
          and o.get("status") in ("new","scored","ready","dispatched")
        ]

        if not existing_for_goal:
            o=generate_opportunity(goal,best)
            p44q.setdefault("opportunities",[]).append(o)
            generated.append(o["opportunity_id"])

        results.append({
          "goal_id":goal["goal_id"],
          "success":True,
          "status":"strategy_selected",
          "strategy_id":best["strategy_id"],
          "strategy_score":best["strategy_score"],
          "progress_pct":goal["progress_pct"]
        })
        audit(results[-1])

    goals["updated_at"]=now()
    registry["updated_at"]=now()
    learning["updated_at"]=now()
    p44q["updated_at"]=now()

    save(GOALS,goals)
    save(STRATS,registry)
    save(LEARN,learning)
    save(P44Q,p44q)

    # Continue opportunity scoring + planning.
    rc44,r44=run([sys.executable,"companyos/phase44ctl","run"])
    rc45,r45=run([sys.executable,"companyos/phase45ctl","run"])

    state={
      "last_run_at":now(),
      "active_goal_count":sum(1 for g in goals.get("goals",[]) if g.get("status")=="active"),
      "strategy_count":len(registry.get("strategies",[])),
      "generated_opportunities":len(generated),
      "completed_goals":completed,
      "last_results":results[-20:]
    }
    save(STATE,state)

    report={
      "generated_at":now(),
      "generated_opportunity_ids":generated,
      "feedback_events_added":feedback_added,
      "phase44":{"return_code":rc44,"result":r44},
      "phase45":{"return_code":rc45,"result":r45},
      "results":results
    }
    save(REPORT,report)

    ok=(rc44==0 and r44.get("success") and rc45==0 and r45.get("success"))

    return {
      "success":bool(ok),
      "status":"phase46_goal_strategy_cycle_complete",
      "report":report
    }

a=sys.argv[1] if len(sys.argv)>1 else "run"

if a=="status":
    r={
      "success":True,
      "status":"phase46_goal_strategy_status",
      "config":load(CFG,{}),
      "state":load(STATE,{}),
      "goals":load(GOALS,{"goals":[]}),
      "strategies":load(STRATS,{"strategies":[]})
    }
else:
    r=cycle()

print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
