#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"outcome_tracker_config.json"; STATE=M/"outcome_tracker_state.json"
REPORT=M/"outcome_tracker_report.json"; HEALTH=M/"outcome_tracker_health.json"
GOALS=M/"goal_strategy_goals.json"; PERF=M/"performance_analytics_report.json"
OPS=M/"autonomous_operations_state.json"; ACTION=M/"internal_action_state.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def measure():
    goals=load(GOALS,{}).get("goals",[])
    perf=load(PERF,{}).get("report",{})
    ops=load(OPS,{})
    actions=load(ACTION,{})
    health=float(perf.get("health_score") or 0)
    jobs=ops.get("jobs",{})
    successes=sum(1 for x in jobs.values() if x.get("last_success") is True)
    failures=sum(1 for x in jobs.values() if x.get("last_success") is False)
    action_failures=int(actions.get("failures",0))
    reliability=round(100*successes/max(1,successes+failures),2)
    goal_rows=[]
    for g in goals:
        base=float(g.get("score",50))
        progress=round(max(0,min(100,base*.45+health*.30+reliability*.25)),2)
        goal_rows.append({"id":g.get("id"),"title":g.get("title"),
                          "rank":g.get("rank"),"progress_score":progress,
                          "status":"on_track" if progress>=70 else "needs_attention"})
    report={"generated_at":now(),"kpis":{
        "operating_health_score":health,"scheduler_reliability_percent":reliability,
        "successful_jobs":successes,"failed_jobs":failures,
        "internal_action_failures":action_failures,"active_goals":len(goals)},
        "goal_outcomes":goal_rows,
        "needs_attention":[x for x in goal_rows if x["status"]=="needs_attention"]}
    save(REPORT,report)
    save(STATE,{"generated_at":now(),"measurement_count":len(goal_rows),
                "average_goal_progress":round(sum(x["progress_score"] for x in goal_rows)/max(1,len(goal_rows)),2)})
    save(HEALTH,{"healthy":True,"last_measured_at":now(),"goal_count":len(goal_rows)})
    return {"success":True,"status":"outcome_measurement_complete","report":report}

def status(): return {"success":True,"status":"outcome_tracker_status",
                      "state":load(STATE,{}),"health":load(HEALTH,{}),
                      "report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=measure() if a=="measure" else status() if a=="status" else {
 "success":False,"status":"unknown_action","allowed":["measure","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
