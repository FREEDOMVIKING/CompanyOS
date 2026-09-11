#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
PERF=MEM/"business_performance_scorecard.json"
OPS=MEM/"generated_business_opportunities.json"
MEMSTATE=MEM/"persistent_memory_state.json"
OUT=MEM/"kpi_goal_tracker.json"
STATE=MEM/"kpi_goal_state.json"
HEALTH=MEM/"kpi_goal_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def update():
    perf=load(PERF,{})
    op_count=int(load(OPS,{}).get("opportunity_count",0) or 0)
    mem_count=int(load(MEMSTATE,{}).get("event_count",0) or 0)
    score=float(perf.get("overall_score",0) or 0)
    goals=[
      {"goal":"business_performance","target":85,"current":score,"unit":"score",
       "status":"met" if score>=85 else "in_progress"},
      {"goal":"active_internal_opportunities","target":5,"current":op_count,"unit":"count",
       "status":"met" if op_count>=5 else "in_progress"},
      {"goal":"persistent_memory_events","target":100,"current":mem_count,"unit":"count",
       "status":"met" if mem_count>=100 else "in_progress"}
    ]
    payload={"generated_at":now(),"goal_count":len(goals),"goals":goals}
    save(OUT,payload);save(STATE,{"last_updated_at":now(),"goal_count":len(goals)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"goal_count":len(goals)})
    return {"success":True,"status":"kpi_goal_update_complete","tracker":payload}

def status():
    return {"success":True,"status":"kpi_goal_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"tracker":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=update() if a=="update" else status() if a=="status" else {"success":False,"allowed":["update","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
