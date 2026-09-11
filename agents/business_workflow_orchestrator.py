#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
TASKS=MEM/"persistent_task_registry.json"
VALIDATED=MEM/"validated_business_opportunities.json"
OUT=MEM/"business_workflow_board.json"
STATE=MEM/"business_workflow_state.json"
HEALTH=MEM/"business_workflow_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def build():
    tasks=load(TASKS,{}).get("tasks",[])
    ops=load(VALIDATED,{}).get("opportunities",[])
    payload={
      "generated_at":now(),
      "workflow_columns":{
        "planned":[x for x in tasks if x.get("status")=="planned"],
        "queued":[x for x in tasks if x.get("status")=="queued"],
        "review":[x for x in tasks if "review" in str(x.get("status",""))],
        "validated_opportunities":[x for x in ops if x.get("validation_status")=="validated_internal_candidate"],
        "needs_evidence":[x for x in ops if x.get("validation_status")=="needs_more_evidence"]
      },
      "external_authority_granted":False
    }
    save(OUT,payload);save(STATE,{"last_built_at":now()})
    save(HEALTH,{"healthy":True,"last_checked_at":now()})
    return {"success":True,"status":"business_workflow_board_complete","board":payload}

def status():
    return {"success":True,"status":"business_workflow_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"board":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
