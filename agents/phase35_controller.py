#!/usr/bin/env python3
import json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
HEALTH=MEM/"phase35_health.json"

def now():return datetime.now(timezone.utc).isoformat()

checks=[]
for name,cmd in [
  ("phase34",[sys.executable,"companyos/phase34ctl"]),
  ("bridge_status",[sys.executable,"companyos/ceotreasurybridgectl","status"])
]:
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=300)
    checks.append({"name":name,"success":p.returncode==0,"stdout":p.stdout[-2000:],"stderr":p.stderr[-500:]})
ok=all(x["success"] for x in checks)
HEALTH.write_text(json.dumps({"healthy":ok,"last_checked_at":now(),"checks":checks},indent=2))
print(json.dumps({"success":ok,"status":"phase35_ceo_treasury_bridge_ready","checks":checks},indent=2))
raise SystemExit(0 if ok else 1)
