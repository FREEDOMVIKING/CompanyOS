#!/usr/bin/env python3
import json, hashlib, sys
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
BASE=M/"drift_baseline.json"; REPORT=M/"drift_report.json"; HEALTH=M/"drift_health.json"
WATCH=[R/"agents",R/"companyos"]

def now(): return datetime.now(timezone.utc).isoformat()
def digest(p):
    try: return hashlib.sha256(p.read_bytes()).hexdigest()
    except: return None
def snapshot():
    out={}
    for root in WATCH:
        if root.exists():
            for p in root.rglob("*"):
                if p.is_file() and "__pycache__" not in p.parts:
                    out[str(p.relative_to(R))]=digest(p)
    return out
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2)); t.replace(p)

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="baseline":
    s=snapshot(); save(BASE,{"created_at":now(),"files":s})
    r={"success":True,"status":"baseline_created","file_count":len(s)}
elif a=="check":
    old=load(BASE,{}).get("files",{}); cur=snapshot()
    added=sorted(set(cur)-set(old)); removed=sorted(set(old)-set(cur))
    changed=sorted(k for k in set(old)&set(cur) if old[k]!=cur[k])
    drift=bool(added or removed or changed)
    rep={"generated_at":now(),"drift_detected":drift,"added":added,"removed":removed,
         "changed":changed,"baseline_file_count":len(old),"current_file_count":len(cur)}
    save(REPORT,rep); save(HEALTH,{"healthy":not drift,"last_checked_at":now(),
                                  "drift_detected":drift,"change_count":len(added)+len(removed)+len(changed)})
    r={"success":True,"status":"drift_check_complete","report":rep}
elif a=="status":
    r={"success":True,"status":"drift_monitor_status",
       "health":load(HEALTH,{}),"report":load(REPORT,{})}
else:
    r={"success":False,"status":"unknown_action","allowed":["baseline","check","status"]}
print(json.dumps(r,indent=2))
