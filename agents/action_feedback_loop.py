#!/usr/bin/env python3
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"action_feedback_config.json"
QUEUE=MEM/"action_queue_report.json"
OUT=MEM/"action_feedback_report.json"
STATE=MEM/"action_feedback_state.json"
HEALTH=MEM/"action_feedback_health.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

def now(): return datetime.now(timezone.utc).isoformat()

def learn():
    cfg=load(CFG,{})
    q=load(QUEUE,{})
    results=q.get("results",[])
    total=len(results)
    failed=sum(1 for x in results if not x.get("success"))
    rate=(failed/total) if total else 0.0

    rec=[]
    if not total:
        rec.append("No completed action-queue results are available yet.")
    elif rate >= float(cfg.get("failure_rate_learning_threshold",0.25)):
        rec.append("Increase review of failing internal actions before expanding automation.")
    else:
        rec.append("Current internal action execution is within the configured feedback threshold.")

    triggered=False
    learning_result=None
    if total and rate >= float(cfg.get("failure_rate_learning_threshold",0.25)) and cfg.get("automatic_internal_learning_trigger"):
        try:
            p=subprocess.run(
                ["python","companyos/learningctl","learn"],
                cwd=ROOT,text=True,capture_output=True,timeout=300
            )
            triggered=True
            learning_result={"return_code":p.returncode,"success":p.returncode==0,
                             "stdout":p.stdout[-2000:],"stderr":p.stderr[-1000:]}
        except Exception as e:
            triggered=True
            learning_result={"success":False,"error":str(e)}

    report={
      "generated_at":now(),
      "actions_evaluated":total,
      "failed_actions":failed,
      "failure_rate":round(rate,4),
      "learning_triggered":triggered,
      "learning_result":learning_result,
      "recommendations":rec,
      "automatic_external_write":False,
      "automatic_code_changes":False,
      "automatic_publication":False,
      "automatic_spending":False,
      "automatic_destructive_actions":False
    }
    save(OUT,report)
    save(STATE,{"generated_at":now(),"actions_evaluated":total,
                "failed_actions":failed,"failure_rate":round(rate,4)})
    save(HEALTH,{"healthy":True,"last_feedback_at":now(),
                 "learning_triggered":triggered})
    return {"success":True,"status":"action_feedback_complete","report":report}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="learn": r=learn()
elif a=="status":
    r={"success":True,"status":"action_feedback_status",
       "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(OUT,{})}
else:r={"success":False,"status":"unknown_action","allowed":["learn","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
