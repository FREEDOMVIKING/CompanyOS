#!/usr/bin/env python3
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"guarded_executor_config.json"
PLAN=MEM/"fused_execution_plan_report.json"
STATE=MEM/"guarded_executor_state.json"
REPORT=MEM/"guarded_executor_report.json"
HEALTH=MEM/"guarded_executor_health.json"

def load(p,d):
    try: return json.loads(p.read_text())
    except Exception: return d
def save(p,d): p.write_text(json.dumps(d,indent=2))
def now(): return datetime.now(timezone.utc).isoformat()

def run():
    cfg=load(CFG,{})
    plan=load(PLAN,{}).get("plan",[])
    allowed=set(cfg.get("allowed_categories",[]))
    maximum=int(cfg.get("maximum_actions_per_run",3))
    results=[]

    for item in plan[:maximum]:
        category=item.get("category")
        cmd=item.get("command")
        if category not in allowed or not isinstance(cmd,list) or not cmd:
            results.append({"action":item.get("action"),"status":"blocked","reason":"guard_policy"})
            continue
        try:
            p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=180)
            results.append({
                "action":item.get("action"),
                "category":category,
                "status":"success" if p.returncode==0 else "failed",
                "returncode":p.returncode,
                "stdout":p.stdout[-4000:],
                "stderr":p.stderr[-2000:]
            })
        except Exception as e:
            results.append({"action":item.get("action"),"status":"failed","error":str(e)})

    report={
      "generated_at":now(),"results":results,
      "executed_count":sum(x["status"]=="success" for x in results),
      "failed_count":sum(x["status"]=="failed" for x in results),
      "blocked_count":sum(x["status"]=="blocked" for x in results),
      "automatic_external_write":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,
      "automatic_publication":False,"automatic_spending":False,
      "automatic_destructive_actions":False
    }
    save(REPORT,report)
    save(STATE,{"last_run_at":now(),"executed_count":report["executed_count"],
                "failed_count":report["failed_count"],"blocked_count":report["blocked_count"]})
    save(HEALTH,{"healthy":report["failed_count"]==0,"last_checked_at":now(),
                 "failure_count":report["failed_count"]})
    return {"success":True,"status":"guarded_execution_complete","report":report}

def status():
    return {"success":True,"status":"guarded_executor_status",
            "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(REPORT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
