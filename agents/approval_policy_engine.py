#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
APPROVALS=MEM/"governed_approval_queue.json"
OUT=MEM/"approval_policy_report.json"
STATE=MEM/"approval_policy_state.json"
HEALTH=MEM/"approval_policy_health.json"

POLICIES={
 "external_launch_or_publication":"explicit_human_approval_required",
 "external_execution_boundary":"explicit_human_approval_required",
 "spending":"explicit_human_approval_required",
 "fund_transfer":"explicit_human_approval_required",
 "code_change":"explicit_human_approval_required",
 "merge":"explicit_human_approval_required",
 "deploy":"explicit_human_approval_required",
 "destructive_action":"explicit_human_approval_required"
}

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def evaluate():
    items=load(APPROVALS,{}).get("items",[])
    rows=[]
    for x in items:
        cls=x.get("action_class")
        rows.append({
          "approval_id":x.get("approval_id"),
          "action_class":cls,
          "policy":POLICIES.get(cls,"explicit_human_approval_required"),
          "current_status":x.get("status","pending"),
          "execution_allowed":False
        })
    payload={"generated_at":now(),"policy_count":len(POLICIES),"evaluated_count":len(rows),
      "policies":POLICIES,"evaluations":rows}
    save(OUT,payload);save(STATE,{"last_evaluated_at":now(),"evaluated_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"evaluated_count":len(rows)})
    return {"success":True,"status":"approval_policy_complete","report":payload}

r=evaluate()
print(json.dumps(r,indent=2))
