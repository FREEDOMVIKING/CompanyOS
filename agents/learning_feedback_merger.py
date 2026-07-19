#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"unified_learning_context.json"
STATE=MEM/"learning_merge_state.json"
HEALTH=MEM/"learning_merge_health.json"

SOURCES=[
 "specialist_performance_profiles.json",
 "validated_insights.json",
 "self_improvement_proposals.json",
 "business_performance_scorecard.json",
 "outcome_tracker_report.json",
 "provider_health_report.json"
]

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)

def merge():
    merged={}
    present=0
    for name in SOURCES:
        p=MEM/name
        if p.exists():
            merged[name]=load(p,{})
            present+=1
    payload={"generated_at":now(),"source_count":present,"sources":merged,
      "purpose":"Unified internal learning context for future prioritization and planning."}
    save(OUT,payload);save(STATE,{"last_merged_at":now(),"source_count":present})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"source_count":present})
    return {"success":True,"status":"learning_feedback_merge_complete","context":payload}

def status():
    return {"success":True,"status":"learning_feedback_merge_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"context":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=merge() if a=="merge" else status() if a=="status" else {"success":False,"allowed":["merge","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
