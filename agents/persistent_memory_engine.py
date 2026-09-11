#!/usr/bin/env python3
from __future__ import annotations
import json, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_config.json"
STORE=MEM/"persistent_business_memory.json"
STATE=MEM/"persistent_memory_state.json"
HEALTH=MEM/"persistent_memory_health.json"

SOURCES=[
  "autonomy_core_report.json",
  "validated_insights.json",
  "ceo_decision_candidates.json",
  "governed_ceo_decisions.json",
  "opportunity_discovery_results.json",
  "portfolio_performance_report.json",
  "business_forecast.json",
  "outcome_tracker_report.json",
  "specialist_runtime_results.json"
]

def now(): return datetime.now(timezone.utc).isoformat()
def load(p:Path,d:Any):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p:Path,d:Any):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2),encoding="utf-8"); t.replace(p)
def digest(x:Any)->str:
    return hashlib.sha256(json.dumps(x,sort_keys=True,default=str).encode()).hexdigest()

def ingest():
    cfg=load(CFG,{})
    store=load(STORE,{"events":[]})
    events=store.setdefault("events",[])
    known={e.get("fingerprint") for e in events}
    added=[]
    for name in SOURCES:
        p=MEM/name
        if not p.exists(): continue
        data=load(p,None)
        if data is None: continue
        fp=digest({"source":name,"data":data})
        if fp in known: continue
        event={"memory_id":fp[:20],"fingerprint":fp,"source":name,"captured_at":now(),"data":data}
        events.append(event); added.append(event); known.add(fp)
    max_events=int(cfg.get("memory_max_events",5000))
    if len(events)>max_events: events[:]=events[-max_events:]
    store["updated_at"]=now(); store["event_count"]=len(events)
    save(STORE,store)
    save(STATE,{"last_ingest_at":now(),"added_count":len(added),"event_count":len(events)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"event_count":len(events)})
    return {"success":True,"status":"persistent_memory_ingest_complete","added_count":len(added),"event_count":len(events)}

def status():
    return {"success":True,"status":"persistent_memory_status",
      "state":load(STATE,{}),"health":load(HEALTH,{}),
      "event_count":load(STORE,{}).get("event_count",0)}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=ingest() if a=="ingest" else status() if a=="status" else {"success":False,"allowed":["ingest","status"]}
print(json.dumps(r,indent=2)); raise SystemExit(0 if r.get("success") else 1)
