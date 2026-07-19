#!/usr/bin/env python3
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory";LAB=ROOT/"platform_lab"
GAPS=MEM/"capability_gap_report.json";OUT=MEM/"platform_architecture_plan.json"
STATE=MEM/"platform_architect_state.json";HEALTH=MEM/"platform_architect_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    proposals=[]
    for g in load(GAPS,{}).get("gaps",[]):
        proposals.append({
          "proposal_id":hashlib.sha256((g["capability"]+"|"+now()).encode()).hexdigest()[:18],
          "capability":g["capability"],
          "objective":f"Close capability gap: {g['capability']}",
          "design":["define interface","build sandbox module","generate tests","run validation","promote if passing"],
          "status":"designed_internal",
          "external_side_effects":False
        })
    payload={"generated_at":now(),"proposal_count":len(proposals),"proposals":proposals}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"proposal_count":len(proposals)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"platform_architecture_complete","plan":payload}
print(json.dumps(run(),indent=2))
