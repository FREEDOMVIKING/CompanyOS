#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
STATE=MEM/"phase26_authority_state.json";REPORT=MEM/"phase26_authority_report.json";HEALTH=MEM/"phase26_authority_health.json"
PIPELINE=[
 ("communications",["python","companyos/communicationsauthorityctl"]),
 ("publication",["python","companyos/publicationauthorityctl"]),
 ("deployment",["python","companyos/deploymentauthorityctl"]),
 ("audit",["python","companyos/executionauditctl"])
]
def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run():
    steps=[];failed=[]
    for name,cmd in PIPELINE:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=600)
        r={"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-2500:],"stderr":p.stderr[-1000:]}
        steps.append({"step":name,"result":r})
        if not r["success"]:failed.append(name)
    report={"generated_at":now(),"failure_count":len(failed),"failed_steps":failed,"steps":steps}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now()})
    return {"success":not failed,"status":"phase26_authority_cycle_complete","report":report}
print(json.dumps(run(),indent=2))
