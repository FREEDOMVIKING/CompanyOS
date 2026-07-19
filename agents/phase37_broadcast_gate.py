#!/usr/bin/env python3
import json,sys
from pathlib import Path

ROOT=Path.home()/"companyos"
P=ROOT/"ceo_memory"/"phase37_safety_config.json"

d=json.loads(P.read_text())
a=sys.argv[1] if len(sys.argv)>1 else "status"

if a=="enable":
    d["broadcast_enabled"]=True
    P.write_text(json.dumps(d,indent=2))
elif a=="disable":
    d["broadcast_enabled"]=False
    P.write_text(json.dumps(d,indent=2))

print(json.dumps({
  "success":True,
  "status":"phase37_broadcast_gate",
  "broadcast_enabled":d.get("broadcast_enabled",False)
},indent=2))
