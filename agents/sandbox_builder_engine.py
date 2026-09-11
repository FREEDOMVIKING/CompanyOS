#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";LAB=ROOT/"platform_lab"
PLAN=MEM/"platform_architecture_plan.json";OUT=MEM/"sandbox_build_report.json"
STATE=MEM/"sandbox_builder_state.json";HEALTH=MEM/"sandbox_builder_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    built=[]
    for p in load(PLAN,{}).get("proposals",[])[:10]:
        sid=p["proposal_id"]
        d=LAB/"sandboxes"/sid;d.mkdir(parents=True,exist_ok=True)
        module=d/"module.py"
        module.write_text(
            "def capability_info():\n"
            f"    return {{'capability': {p['capability']!r}, 'sandbox': True, 'status': 'prototype'}}\n"
        )
        test=d/"test_module.py"
        test.write_text(
            "from module import capability_info\n"
            "x=capability_info()\n"
            "assert x['sandbox'] is True\n"
            "assert x['status']=='prototype'\n"
            "print('PASS')\n"
        )
        built.append({"proposal_id":sid,"capability":p["capability"],"sandbox_dir":str(d),"status":"built"})
    payload={"generated_at":now(),"build_count":len(built),"builds":built}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"build_count":len(built)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"sandbox_build_complete","report":payload}
print(json.dumps(run(),indent=2))
