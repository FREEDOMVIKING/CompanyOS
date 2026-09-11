#!/usr/bin/env python3
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"cycle_supervisor_config.json"
CYCLE=MEM/"control_cycle_state.json"
STATE=MEM/"cycle_supervisor_state.json"
REPORT=MEM/"cycle_supervisor_report.json"
HEALTH=MEM/"cycle_supervisor_health.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def now():return datetime.now(timezone.utc).isoformat()
def cmd(a):
    try:
        p=subprocess.run(a,cwd=ROOT,text=True,capture_output=True,timeout=300)
        return {"success":p.returncode==0,"return_code":p.returncode,
                "stdout":p.stdout[-2000:],"stderr":p.stderr[-1000:]}
    except Exception as e:return {"success":False,"error":str(e)}

def supervise():
    cfg=load(CFG,{})
    cyc=load(CYCLE,{})
    prev=load(STATE,{"consecutive_failures":0})
    failures=int(prev.get("consecutive_failures",0))

    if cyc.get("cycle_success") is False: failures+=1
    elif cyc.get("cycle_success") is True: failures=0

    actions=[]
    if failures>=int(cfg.get("max_consecutive_failures",3)) and cfg.get("automatic_internal_recovery",True):
        actions.append({"action":"health_check","result":cmd(["python","companyos/healthctl","run"])})
        actions.append({"action":"scheduler_restart","result":cmd(["python","companyos/operationsctl","restart"])})
        actions.append({"action":"preflight_recheck","result":cmd(["python","companyos/preflightctl","run"])})
        failures=0

    healthy=all(x["result"].get("success",False) for x in actions) if actions else True
    report={"generated_at":now(),"observed_cycle":cyc,"recovery_actions":actions,
            "consecutive_failures":failures,
            "automatic_external_write":False,"automatic_code_changes":False,
            "automatic_merge":False,"automatic_deploy":False,
            "automatic_spending":False,"automatic_destructive_actions":False}
    save(REPORT,report)
    save(STATE,{"last_supervision_at":now(),"consecutive_failures":failures,
                "recovery_action_count":len(actions)})
    save(HEALTH,{"healthy":healthy,"last_checked_at":now(),
                 "recovery_action_count":len(actions)})
    return {"success":healthy,"status":"cycle_supervision_complete","report":report}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="run":r=supervise()
elif a=="status":r={"success":True,"status":"cycle_supervisor_status",
                    "state":load(STATE,{}),"health":load(HEALTH,{}),"report":load(REPORT,{})}
else:r={"success":False,"status":"unknown_action","allowed":["run","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
