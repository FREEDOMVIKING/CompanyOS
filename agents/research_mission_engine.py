#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_bundle3_config.json"
PLAN=MEM/"strategic_30_day_plan.json"
OUT=MEM/"research_mission_queue.json"
STATE=MEM/"research_mission_state.json"
HEALTH=MEM/"research_mission_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def mid(x):return hashlib.sha256(x.encode()).hexdigest()[:18]

def generate():
    cfg=load(CFG,{})
    actions=load(PLAN,{}).get("actions",[])
    rows=[]
    for a in actions[:int(cfg.get("maximum_research_missions",15))]:
        title=a.get("title","Untitled opportunity")
        rows.append({
          "mission_id":mid(title),
          "title":f"Research: {title}",
          "source_action_id":a.get("id"),
          "questions":[
            "What evidence supports this opportunity?",
            "What are the main risks and failure modes?",
            "What is the smallest practical validation step?",
            "What internal capabilities or dependencies are required?"
          ],
          "status":"queued_internal_research",
          "execution_boundary":"internal_non_destructive_only",
          "created_at":now()
        })
    payload={"generated_at":now(),"mission_count":len(rows),"missions":rows}
    save(OUT,payload);save(STATE,{"last_generated_at":now(),"mission_count":len(rows)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"mission_count":len(rows)})
    return {"success":True,"status":"research_mission_generation_complete","queue":payload}

def status():
    return {"success":True,"status":"research_mission_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"queue":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=generate() if a=="generate" else status() if a=="status" else {"success":False,"allowed":["generate","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
