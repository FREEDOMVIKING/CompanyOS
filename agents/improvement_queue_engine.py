#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_bundle2_config.json"
SOURCE=MEM/"self_improvement_proposals.json"
OUT=MEM/"governed_improvement_queue.json"
STATE=MEM/"improvement_queue_state.json"
HEALTH=MEM/"improvement_queue_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def queue():
    cfg=load(CFG,{})
    source=load(SOURCE,{}).get("proposals",[])
    existing=load(OUT,{"items":[]}).get("items",[])
    seen={x.get("id") for x in existing}
    maximum=int(cfg.get("maximum_improvement_queue_items",25))
    added=[]
    for p in source:
        if len(existing)>=maximum:break
        if p.get("id") in seen:continue
        item=dict(p)
        item["queue_status"]="awaiting_governed_internal_review"
        item["execution_authority"]="none"
        item["queued_at"]=now()
        existing.append(item);added.append(item);seen.add(p.get("id"))
    payload={"generated_at":now(),"item_count":len(existing),"items":existing,
      "note":"Queue does not authorize code changes, merge, deploy, spending, or destructive actions."}
    save(OUT,payload);save(STATE,{"last_queued_at":now(),"added_count":len(added),"item_count":len(existing)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"item_count":len(existing)})
    return {"success":True,"status":"improvement_queue_complete","added_count":len(added),"queue":payload}

def status():
    return {"success":True,"status":"improvement_queue_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"queue":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=queue() if a=="queue" else status() if a=="status" else {"success":False,"allowed":["queue","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
