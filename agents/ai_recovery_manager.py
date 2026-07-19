#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"ai_recovery_report.json"; STATE=MEM/"ai_recovery_state.json"; HEALTH=MEM/"ai_recovery_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def call(cmd):
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=600)
    return {"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-2000:],"stderr":p.stderr[-1000:]}

def run():
    steps=[
      {"step":"local_ai_guard","result":call([sys.executable,"companyos/localaiguardctl","run"])},
      {"step":"provider_health","result":call([sys.executable,"companyos/aiproviderhealthctl","run"])},
      {"step":"task_router","result":call([sys.executable,"companyos/aitaskrouterctl","run"])}
    ]
    failed=[s["step"] for s in steps if not s["result"]["success"]]
    payload={"generated_at":now(),"failure_count":len(failed),"failed_steps":failed,"steps":steps}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now()})
    return {"success":not failed,"status":"ai_recovery_complete","report":payload}

print(json.dumps(run(),indent=2))
