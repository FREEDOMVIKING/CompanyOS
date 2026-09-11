#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
STATE=MEM/"phase32_state.json";HEALTH=MEM/"phase32_health.json";REPORT=MEM/"phase32_report.json"

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

steps=[];failed=[]
for name,cmd in [
 ("multi_asset_balances",["python","companyos/multiassetbalancectl"]),
 ("signing_queue",["python","companyos/transactionsigningqueuectl"])
]:
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=300)
    r={"success":p.returncode==0,"return_code":p.returncode,"stdout":p.stdout[-2500:],"stderr":p.stderr[-1000:]}
    steps.append({"step":name,"result":r})
    if not r["success"]:failed.append(name)

report={"generated_at":now(),"failure_count":len(failed),"failed_steps":failed,"steps":steps}
save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now()})
print(json.dumps({"success":not failed,"status":"phase32_transaction_policy_complete","report":report},indent=2))
raise SystemExit(0 if not failed else 1)
