#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
STATE=MEM/"phase29_state.json";HEALTH=MEM/"phase29_health.json";REPORT=MEM/"phase29_report.json"

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

steps=[]
for name,cmd in [
 ("deposit_monitor",["python","companyos/depositmonitorctl"]),
 ("policy_smoke_test",["python","companyos/treasurypolicyctl","1000","SOL","solana","demo-destination"])
]:
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=300)
    steps.append({"step":name,"success":p.returncode==0,"stdout":p.stdout[-1500:],"stderr":p.stderr[-500:]})
failed=[x["step"] for x in steps if not x["success"]]
report={"generated_at":now(),"failure_count":len(failed),"failed_steps":failed,"steps":steps}
save(REPORT,report);save(STATE,{"last_run_at":now(),"failure_count":len(failed),"failed_steps":failed});save(HEALTH,{"healthy":not failed,"last_checked_at":now()})
print(json.dumps({"success":not failed,"status":"phase29_crypto_treasury_core_ready","report":report},indent=2))
