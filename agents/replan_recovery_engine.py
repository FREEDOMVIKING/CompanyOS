#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
PH24=MEM/"phase24_report.json"
AUTONOMY=MEM/"autonomy_core_report.json"
OUT=MEM/"replan_recovery_actions.json"
STATE=MEM/"replan_recovery_state.json"
HEALTH=MEM/"replan_recovery_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def run():
    failures=[]
    for source,path in [("phase24",PH24),("autonomy",AUTONOMY)]:
        d=load(path,{})
        for step in d.get("failed_steps",[]) or []:
            failures.append({"source":source,"step":step})
    actions=[]
    for f in failures:
        actions.append({
          "source":f["source"],"failed_step":f["step"],
          "recommended_action":"Re-run prerequisite health checks, refresh upstream state, then retry the failed internal step.",
          "status":"replan_recommended",
          "external_action":False
        })
    payload={"generated_at":now(),"failure_count":len(failures),"replan_action_count":len(actions),"actions":actions}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"failure_count":len(failures)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"failure_count":len(failures)})
    return {"success":True,"status":"replan_recovery_complete","report":payload}

def status():
    return {"success":True,"status":"replan_recovery_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
