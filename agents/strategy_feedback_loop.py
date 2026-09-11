#!/usr/bin/env python3
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"strategy_feedback_config.json"
OUT=M/"outcome_tracker_report.json"
GOALS=M/"goal_strategy_goals.json"
STATE=M/"strategy_feedback_state.json"
REPORT=M/"strategy_feedback_report.json"
HEALTH=M/"strategy_feedback_health.json"
HALT=M/"HALT_AUTONOMY"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run(cmd):
    try:
        p=subprocess.run(cmd,cwd=R,text=True,capture_output=True,timeout=300)
        return {"success":p.returncode==0,"return_code":p.returncode,
                "stdout":p.stdout[-2500:],"stderr":p.stderr[-1200:]}
    except Exception as e:return {"success":False,"error":str(e)}

def adapt():
    cfg=load(CFG,{})
    if not cfg.get("enabled",True):
        return {"success":False,"status":"strategy_feedback_disabled"}
    if HALT.exists():
        return {"success":False,"status":"autonomy_halted"}

    outcomes=load(OUT,{})
    goals=load(GOALS,{}).get("goals",[])
    rows=outcomes.get("goal_outcomes",[])
    low=float(cfg.get("low_progress_threshold",60))
    high=float(cfg.get("high_progress_threshold",80))

    signals=[]
    for row in rows:
        score=float(row.get("progress_score",0))
        if score<low:
            signals.append({"goal_id":row.get("id"),"signal":"increase_attention",
                            "progress_score":score})
        elif score>=high:
            signals.append({"goal_id":row.get("id"),"signal":"maintain_or_expand",
                            "progress_score":score})

    avg=round(sum(float(x.get("progress_score",0)) for x in rows)/max(1,len(rows)),2)
    actions=[]
    if cfg.get("automatic_learning_trigger",True):
        actions.append({"action":"learning-run",
                        "result":run([sys.executable,"companyos/learningctl","learn"])})
    if cfg.get("automatic_goal_refresh",True):
        actions.append({"action":"goal-refresh",
                        "result":run([sys.executable,"companyos/goalctl","generate"])})

    report={"generated_at":now(),"average_goal_progress":avg,
            "signals":signals,"feedback_actions":actions,
            "goal_count":len(goals)}
    save(REPORT,report)
    save(STATE,{"generated_at":now(),"cycle_count":int(load(STATE,{}).get("cycle_count",0))+1,
                "average_goal_progress":avg,"signal_count":len(signals)})
    failures=[a for a in actions if not a["result"].get("success")]
    save(HEALTH,{"healthy":not failures,"last_run_at":now(),
                 "signal_count":len(signals),"failure_count":len(failures)})
    return {"success":not failures,"status":"strategy_feedback_complete","report":report}

def status():
    return {"success":True,"status":"strategy_feedback_status",
            "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=adapt() if a=="adapt" else status() if a=="status" else {
 "success":False,"status":"unknown_action","allowed":["adapt","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
