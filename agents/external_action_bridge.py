#!/usr/bin/env python3
import json,sys,subprocess
from pathlib import Path
ROOT=Path.home()/"companyos"
kind=sys.argv[1] if len(sys.argv)>1 else "status"
if kind=="status":
    print(json.dumps({"success":True,"status":"external_action_bridge_ready"},indent=2));raise SystemExit(0)
payload=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
p=subprocess.run([sys.executable,"companyos/liveexecutionctl","execute",kind,json.dumps(payload)],cwd=ROOT,text=True,capture_output=True,timeout=300)
print(p.stdout or json.dumps({"success":False,"stderr":p.stderr},indent=2))
raise SystemExit(p.returncode)
