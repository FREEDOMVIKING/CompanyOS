#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path.home()/"companyos";P=ROOT/"ceo_memory"/"phase34_autonomous_treasury_config.json"
d=json.loads(P.read_text())
a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="on":d["kill_switch"]=True;P.write_text(json.dumps(d,indent=2))
elif a=="off":d["kill_switch"]=False;P.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"status":"treasury_kill_switch","kill_switch":d.get("kill_switch",False)},indent=2))
