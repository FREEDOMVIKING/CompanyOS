#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";LAB=ROOT/"platform_lab"
BUILDS=MEM/"sandbox_build_report.json";OUT=MEM/"self_test_report.json"
STATE=MEM/"self_test_state.json";HEALTH=MEM/"self_test_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    rows=[]
    for b in load(BUILDS,{}).get("builds",[]):
        d=Path(b["sandbox_dir"])
        p=subprocess.run([sys.executable,"test_module.py"],cwd=d,text=True,capture_output=True,timeout=60)
        rows.append({"proposal_id":b["proposal_id"],"capability":b["capability"],"passed":p.returncode==0,
                     "return_code":p.returncode,"stdout":p.stdout[-500:],"stderr":p.stderr[-500:]})
    passed=sum(1 for x in rows if x["passed"])
    payload={"generated_at":now(),"test_count":len(rows),"passed_count":passed,
             "pass_rate":(passed/len(rows)) if rows else 1.0,"tests":rows}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"test_count":len(rows),"passed_count":passed});save(HEALTH,{"healthy":passed==len(rows),"last_checked_at":now()})
    return {"success":passed==len(rows),"status":"self_test_complete","report":payload}
print(json.dumps(run(),indent=2))
