#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
STATE=MEM/"phase24_bundle3_state.json"; REPORT=MEM/"phase24_bundle3_report.json"; HEALTH=MEM/"phase24_bundle3_health.json"

PIPELINE=[
 ("phase24_bundle2",["python","companyos/phase24bundle2ctl","run"]),
 ("approval_gateway",["python","companyos/approvalgatewayctl","build"]),
 ("action_registry",["python","companyos/actionregistryctl","sync"]),
 ("execution_receipts",["python","companyos/executionreceiptctl","build"]),
 ("connector_readiness",["python","companyos/connectorreadinessctl","check"]),
 ("observability",["python","companyos/observabilityctl","run"]),
 ("incident_triage",["python","companyos/incidentctl","run"]),
 ("control_center",["python","companyos/controlcenterctl","show"])
]

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def call(cmd):
    try:
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=2400)
        return {"success":p.returncode==0,"return_code":p.returncode,
          "stdout":p.stdout[-4000:],"stderr":p.stderr[-2000:]}
    except Exception as e:return {"success":False,"error":str(e)}

def run():
    steps=[];failed=[]
    for name,cmd in PIPELINE:
        r=call(cmd);steps.append({"step":name,"result":r})
        if not r.get("success"):failed.append(name)
    report={"generated_at":now(),"steps":steps,"failure_count":len(failed),"failed_steps":failed}
    save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed})
    save(HEALTH,{"healthy":not failed,"last_checked_at":now(),"failure_count":len(failed)})
    return {"success":not failed,"status":"phase24_bundle3_cycle_complete","report":report}

def status():
    def load(p):
        try:return json.loads(p.read_text())
        except:return {}
    return {"success":True,"status":"phase24_bundle3_status","state":load(STATE),"health":load(HEALTH)}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=run() if a=="run" else status() if a=="status" else {"success":False,"allowed":["run","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
