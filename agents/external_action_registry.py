#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
APPROVALS=MEM/"governed_approval_queue.json"
OUT=MEM/"external_action_registry.json"
STATE=MEM/"external_action_registry_state.json"
HEALTH=MEM/"external_action_registry_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def sync():
    approvals=load(APPROVALS,{}).get("items",[])
    rows=[]
    for a in approvals:
        rows.append({
          "action_id":a.get("approval_id"),
          "project_id":a.get("project_id"),
          "title":a.get("title"),
          "action_class":a.get("action_class"),
          "approval_status":a.get("status","pending"),
          "execution_status":"blocked_until_explicit_approval",
          "external_execution_allowed":False,
          "updated_at":now()
        })
    payload={"generated_at":now(),"action_count":len(rows),"actions":rows}
    save(OUT,payload);save(STATE,{"last_synced_at":now(),"action_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"action_count":len(rows)})
    return {"success":True,"status":"external_action_registry_complete","registry":payload}

def status():
    return {"success":True,"status":"external_action_registry_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"registry":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=sync() if a=="sync" else status() if a=="status" else {"success":False,"allowed":["sync","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
