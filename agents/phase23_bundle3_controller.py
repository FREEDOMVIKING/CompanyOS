#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase23_bundle3_state.json"; REPORT=MEM/"phase23_bundle3_report.json"; HEALTH=MEM/"phase23_bundle3_health.json"

PIPELINE=[
 ("bundle2",["python","companyos/phase23bundle2ctl","run"]),
 ("strategic_plan",["python","companyos/strategicplanctl","build"]),
 ("portfolio_resources",["python","companyos/portfoliocapitalctl","allocate"]),
 ("research_missions",["python","companyos/researchmissionctl","generate"]),
 ("kpi_goals",["python","companyos/kpigoalctl","update"]),
 ("learning_merge",["python","companyos/learningmergectl","merge"]),
 ("action_board",["python","companyos/actionboardctl","show"])
]

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def call(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=1800)
        return {"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-3500:],"stderr":p.stderr[-1500:]}
    except Exception as e:return {"success":False,"error":str(e)}

def run():
    steps=[];failed=[]
    for name,cmd in PIPELINE:
        r=call(cmd);steps.append({"step":name,"result":r})
        if not r.get("success"):failed.append(name)
    report={"generated_at":now(),"steps":steps,"failure_count":len(failed),"failed_steps":failed}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed})
    save(HEALTH,{"healthy":not failed,"last_checked_at":now(),"failure_count":len(failed)})
    return {"success":not failed,"status":"phase23_bundle3_cycle_complete","report":report}

def status():
    def load(p):
        try:return json.loads(p.read_text())
        except:return {}
    return {"success":True,"status":"phase23_bundle3_status","state":load(STATE),"health":load(HEALTH)}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
