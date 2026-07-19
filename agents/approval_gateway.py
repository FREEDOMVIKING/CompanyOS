#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase24_bundle3_config.json"
INCUBATION=MEM/"business_incubation_portfolio.json"
PROJECTS=MEM/"project_execution_registry.json"
OUT=MEM/"governed_approval_queue.json"
STATE=MEM/"approval_gateway_state.json"
HEALTH=MEM/"approval_gateway_health.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def aid(seed):return hashlib.sha256(str(seed).encode()).hexdigest()[:20]

def build():
    cfg=load(CFG,{})
    existing=load(OUT,{"items":[]}).get("items",[])
    seen={x.get("approval_id") for x in existing}
    added=[]

    for c in load(INCUBATION,{}).get("candidates",[]):
        if c.get("external_launch_authorized") is True:
            continue
        approval_id=aid("launch|"+str(c.get("project_id")))
        if approval_id in seen: continue
        item={
          "approval_id":approval_id,
          "project_id":c.get("project_id"),
          "title":c.get("title"),
          "action_class":"external_launch_or_publication",
          "requested_authority":"explicit_human_approval_required",
          "status":"pending",
          "created_at":now()
        }
        existing.append(item);added.append(item);seen.add(approval_id)

    for p in load(PROJECTS,{}).get("projects",[]):
        approval_id=aid("execution|"+str(p.get("project_id")))
        if approval_id in seen: continue
        item={
          "approval_id":approval_id,
          "project_id":p.get("project_id"),
          "title":p.get("title"),
          "action_class":"external_execution_boundary",
          "requested_authority":"explicit_human_approval_required",
          "status":"pending",
          "created_at":now()
        }
        existing.append(item);added.append(item);seen.add(approval_id)

    existing=existing[:int(cfg.get("maximum_pending_approvals",100))]
    payload={"generated_at":now(),"item_count":len(existing),"items":existing}
    save(OUT,payload)
    save(STATE,{"last_built_at":now(),"added_count":len(added),"item_count":len(existing)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"item_count":len(existing)})
    return {"success":True,"status":"approval_gateway_complete","added_count":len(added),"queue":payload}

def status():
    return {"success":True,"status":"approval_gateway_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"queue":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
