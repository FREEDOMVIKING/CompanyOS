#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
SRC=MEM/"specialist_runtime_results.json"
OUT=MEM/"ai_provenance_log.json"
STATE=MEM/"ai_provenance_state.json"
HEALTH=MEM/"ai_provenance_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def run():
    rows=[]
    for r in load(SRC,{}).get("results",[]):
        actual=r.get("actual_result",{})
        if not isinstance(actual,dict): continue
        rows.append({
          "work_id":r.get("work_id"),
          "provider_used":actual.get("_provider_used","unknown"),
          "primary_failure":actual.get("_primary_failure"),
          "confidence":actual.get("confidence"),
          "completed_at":r.get("completed_at"),
          "execution_boundary":r.get("execution_boundary")
        })
    payload={"generated_at":now(),"event_count":len(rows),"events":rows[-500:]}
    save(OUT,payload);save(STATE,{"last_run_at":now(),"event_count":len(rows)});save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"ai_provenance_complete","report":payload}

print(json.dumps(run(),indent=2))
