#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
STATE=MEM/"phase27_state.json";HEALTH=MEM/"phase27_health.json"
def now():return datetime.now(timezone.utc).isoformat()
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def run():
    p=subprocess.run([sys.executable,"companyos/liveexecutionctl","status"],cwd=ROOT,text=True,capture_output=True,timeout=60)
    ok=p.returncode==0
    save(STATE,{"last_run_at":now(),"failure_count":0 if ok else 1})
    save(HEALTH,{"healthy":ok,"last_checked_at":now()})
    return {"success":ok,"status":"phase27_execution_connector_core_ready","router":p.stdout}
print(json.dumps(run(),indent=2))
