#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase23_state.json"; REPORT=MEM/"phase23_report.json"; HEALTH=MEM/"phase23_health.json"

PIPELINE=[
 ("autonomy",["python","companyos/autonomyctl","run"]),
 ("memory",["python","companyos/memoryctl","ingest"]),
 ("signals",["python","companyos/businesssignalctl","run"]),
 ("opportunities",["python","companyos/opportunitygenctl","generate"]),
 ("performance",["python","companyos/performancecorectl","score"]),
 ("improvements",["python","companyos/improvementproposalctl","propose"]),
 ("dashboard",["python","companyos/executivedashboardctl","show"])
]

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def call(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=1200)
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
    return {"success":not failed,"status":"phase23_adaptive_business_intelligence_cycle_complete","report":report}

def status():
    try:s=json.loads(STATE.read_text())
    except:s={}
    try:h=json.loads(HEALTH.read_text())
    except:h={}
    return {"success":True,"status":"phase23_status","state":s,"health":h}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
