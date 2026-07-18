#!/usr/bin/env python3
import json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
CFG=MEM/"governance_config.json"
QUEUE=MEM/"governance_queue.json"
STATE=MEM/"governance_state.json"
HEALTH=MEM/"governance_health.json"
ACTIONQ=MEM/"internal_action_queue.json"
DECISIONS=MEM/"ceo_decision_queue.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try: return json.loads(p.read_text())
    except Exception: return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2)); t.replace(p)

def classify():
    cfg=load(CFG,{})
    actions=load(ACTIONQ,{}).get("actions",[])
    decisions=load(DECISIONS,{}).get("decisions",[])
    routed=[]

    for a in actions:
        if a.get("status") != "pending": continue
        external=bool(a.get("external_action",False))
        routed.append({
            "source":"internal_action",
            "id":a.get("id"),
            "title":a.get("action"),
            "classification":"owner_approval_required" if external else "internal_auto_allowed",
            "reason":"External effect requires approval." if external else "Internal allowlisted action."
        })

    for d in decisions:
        if d.get("status") != "pending": continue
        routed.append({
            "source":"ceo_decision",
            "id":d.get("id"),
            "title":d.get("title"),
            "classification":"owner_review",
            "reason":"Pending CEO decision."
        })

    out={"generated_at":now(),"items":routed,"count":len(routed)}
    save(QUEUE,out)
    save(STATE,{
        "generated_at":now(),
        "total_items":len(routed),
        "internal_auto_allowed":sum(x["classification"]=="internal_auto_allowed" for x in routed),
        "owner_review_required":sum(x["classification"]!="internal_auto_allowed" for x in routed)
    })
    save(HEALTH,{"healthy":True,"last_run_at":now(),"item_count":len(routed)})
    return {"success":True,"status":"governance_routing_complete","queue":out}

def status():
    return {"success":True,"status":"governance_status","config":load(CFG,{}),
            "state":load(STATE,{}),"health":load(HEALTH,{})}

action=sys.argv[1] if len(sys.argv)>1 else "status"
result=classify() if action=="classify" else status() if action=="status" else {
    "success":False,"status":"unknown_action","allowed":["classify","status"]}
print(json.dumps(result,indent=2))
raise SystemExit(0 if result.get("success") else 1)
