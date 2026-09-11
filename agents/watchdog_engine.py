#!/usr/bin/env python3
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"watchdog_config.json"; CYCLE=M/"control_cycle_state.json"
STATE=M/"watchdog_state.json"; HEALTH=M/"watchdog_health.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def now():return datetime.now(timezone.utc)
def call(args):
    try:
        p=subprocess.run(args,cwd=R,text=True,capture_output=True,timeout=600)
        return {"success":p.returncode==0,"return_code":p.returncode,
                "stdout":p.stdout[-1500:],"stderr":p.stderr[-1000:]}
    except Exception as e:return {"success":False,"error":str(e)}
def age_seconds(v):
    try:return max(0,(now()-datetime.fromisoformat(v.replace("Z","+00:00"))).total_seconds())
    except:return None

def run():
    cfg=load(CFG,{})
    cyc=load(CYCLE,{})
    age=age_seconds(cyc.get("last_cycle_at",""))
    stale=age is None or age>cfg.get("heartbeat_stale_seconds",5400)
    actions=[]
    if stale and cfg.get("automatic_scheduler_restart",True):
        actions.append({"action":"restart_scheduler","result":call(["python","companyos/operationsctl","restart"])})
    if stale and cfg.get("automatic_control_cycle_recovery",True):
        actions.append({"action":"recover_control_cycle","result":call(["python","companyos/controlcyclectl","run"])})
    healthy=not stale or all(a["result"].get("success",False) for a in actions)
    s={"last_checked_at":now().isoformat(),"heartbeat_age_seconds":age,
       "heartbeat_stale":stale,"recovery_actions":actions}
    save(STATE,s);save(HEALTH,{"healthy":healthy,**s})
    return {"success":healthy,"status":"watchdog_check_complete","state":s}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="run":r=run()
elif a=="status":r={"success":True,"status":"watchdog_status",
                    "state":load(STATE,{}),"health":load(HEALTH,{})}
else:r={"success":False,"status":"unknown_action","allowed":["run","status"]}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
