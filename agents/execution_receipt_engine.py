#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
RESULTS=MEM/"specialist_runtime_results.json"
OUT=MEM/"execution_receipts.json"
STATE=MEM/"execution_receipt_state.json"
HEALTH=MEM/"execution_receipt_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def rid(seed):return hashlib.sha256(str(seed).encode()).hexdigest()[:20]

def build():
    rows=load(RESULTS,{}).get("results",[])
    receipts=[]
    for r in rows[-500:]:
        if r.get("status")!="completed":continue
        receipts.append({
          "receipt_id":rid(r.get("work_id")),
          "work_id":r.get("work_id"),
          "project_id":r.get("opportunity_id"),
          "action_type":r.get("action_type"),
          "status":"completed_internal",
          "execution_boundary":r.get("execution_boundary","internal_non_destructive_only"),
          "completed_at":r.get("completed_at"),
          "recorded_at":now()
        })
    payload={"generated_at":now(),"receipt_count":len(receipts),"receipts":receipts}
    save(OUT,payload);save(STATE,{"last_built_at":now(),"receipt_count":len(receipts)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"receipt_count":len(receipts)})
    return {"success":True,"status":"execution_receipts_complete","report":payload}

def status():
    return {"success":True,"status":"execution_receipt_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"report":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
