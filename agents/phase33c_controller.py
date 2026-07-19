#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
STATE=MEM/"phase33c_state.json";HEALTH=MEM/"phase33c_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

p=subprocess.run([sys.executable,"companyos/solanasignervalidationctl"],cwd=ROOT,text=True,capture_output=True,timeout=180)
ok=p.returncode==0
state={
    "last_run_at":now(),
    "failure_count":0 if ok else 1,
    "stdout":p.stdout[-4000:],
    "stderr":p.stderr[-1000:]
}
save(STATE,state)
save(HEALTH,{"healthy":ok,"last_checked_at":now()})
print(json.dumps({"success":ok,"status":"phase33c_validation_complete","state":state},indent=2))
raise SystemExit(0 if ok else 1)
