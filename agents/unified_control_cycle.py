#!/usr/bin/env python3
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"control_cycle_config.json"
REPORT=MEM/"control_cycle_report.json"
STATE=MEM/"control_cycle_state.json"
HEALTH=MEM/"control_cycle_health.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2)); t.replace(p)
def now():return datetime.now(timezone.utc).isoformat()
def call(args):
    try:
        p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=600)
        return {"success":p.returncode==0,"return_code":p.returncode,
                "stdout":p.stdout[-3000:],"stderr":p.stderr[-1500:]}
    except Exception as e:return {"success":False,"error":str(e)}

def cycle():
    cfg=load(CFG,{})
    steps=[]
    plan=[
      ("preflight",["python","companyos/preflightctl","run"]),
      ("action_queue",["python","companyos/actionqueuectl","run"]),
      ("feedback",["python","companyos/actionfeedbackctl","learn"])
    ]
    for name,cmd in plan:
        r=call(cmd); steps.append({"component":name,"result":r,"success":r.get("success",False)})
        if not r.get("success") and not cfg.get("continue_on_component_failure",True):break
    failures=[x for x in steps if not x["success"]]
    report={
      "generated_at":now(),"components":steps,"failure_count":len(failures),
      "cycle_success":len(failures)==0,
      "automatic_external_write":False,"automatic_code_changes":False,
      "automatic_merge":False,"automatic_deploy":False,
      "automatic_publication":False,"automatic_spending":False,
      "automatic_destructive_actions":False
    }
    save(REPORT,report)
    save(STATE,{"last_cycle_at":now(),"cycle_success":len(failures)==0,
                "failure_count":len(failures)})
    save(HEALTH,{"healthy":len(failures)==0,"last_checked_at":now(),
                 "failure_count":len(failures)})
    return {"success":len(failures)==0,"status":"unified_control_cycle_complete","report":report}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="run":r=cycle()
elif a=="status":r={"success":True,"status":"unified_control_cycle_status",
                    "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(REPORT,{})}
else:r={"success":False,"status":"unknown_action","allowed":["run","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
