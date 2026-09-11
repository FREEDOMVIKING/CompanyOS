#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase25_bundle2_state.json"; REPORT=MEM/"phase25_bundle2_report.json"; HEALTH=MEM/"phase25_bundle2_health.json"

PIPELINE=[
 ("phase25_bundle1",["python","companyos/phase25bundle1ctl","run"]),
 ("model_registry",["python","companyos/modelcapabilityctl","run"]),
 ("task_decomposition",["python","companyos/taskdecompositionctl","run"]),
 ("specialist_delegation",["python","companyos/specialistdelegationctl","run"]),
 ("result_validation",["python","companyos/resultvalidationctl","run"]),
 ("ceo_synthesis",["python","companyos/ceosynthesisctl","run"]),
 ("resource_governor",["python","companyos/airesourcegovernorctl","run"])
]

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def call(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=2400)
        return {"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-3500:],"stderr":p.stderr[-1500:]}
    except Exception as e:return {"success":False,"error":str(e)}

def run():
    steps=[];failed=[]
    for name,cmd in PIPELINE:
        r=call(cmd);steps.append({"step":name,"result":r})
        if not r.get("success"):failed.append(name)
    report={"generated_at":now(),"steps":steps,"failure_count":len(failed),"failed_steps":failed}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now(),"failure_count":len(failed)})
    return {"success":not failed,"status":"phase25_bundle2_cycle_complete","report":report}

def status():
    def l(p):
        try:return json.loads(p.read_text())
        except:return {}
    return {"success":True,"status":"phase25_bundle2_status","state":l(STATE),"health":l(HEALTH)}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status()
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
