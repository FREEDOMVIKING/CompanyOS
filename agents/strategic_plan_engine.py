#!/usr/bin/env python3
from __future__ import annotations
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase23_bundle3_config.json"
OPS=MEM/"generated_business_opportunities.json"
PERF=MEM/"business_performance_scorecard.json"
BRIEF=MEM/"executive_briefing.json"
OUT=MEM/"strategic_30_day_plan.json"
STATE=MEM/"strategic_plan_state.json"
HEALTH=MEM/"strategic_plan_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2),encoding="utf-8");t.replace(p)
def sid(text):return hashlib.sha256(text.encode()).hexdigest()[:16]

def build():
    cfg=load(CFG,{})
    ops=load(OPS,{}).get("opportunities",[])
    perf=load(PERF,{})
    brief=load(BRIEF,{})
    actions=[]
    for i,o in enumerate(ops[:10],1):
        title=o.get("title") or f"Opportunity {i}"
        actions.append({
          "id":sid(title),
          "priority":i,
          "title":title,
          "category":o.get("category","growth"),
          "score":o.get("score",50),
          "objective":"Advance the opportunity through internal research, validation, planning, and governed execution preparation.",
          "status":"planned_internal",
          "authority":"internal_non_destructive_only"
        })
    if float(perf.get("overall_score",100) or 100)<85:
        actions.append({
          "id":sid("raise-business-performance"),
          "priority":len(actions)+1,
          "title":"Raise business performance score",
          "category":"optimization",
          "score":85,
          "objective":"Improve the weakest measured KPI dimensions using internal analysis and measured feedback.",
          "status":"planned_internal",
          "authority":"internal_non_destructive_only"
        })
    actions=actions[:int(cfg.get("maximum_strategic_actions",20))]
    payload={
      "generated_at":now(),
      "planning_horizon_days":int(cfg.get("planning_horizon_days",30)),
      "business_performance_score":perf.get("overall_score"),
      "recommended_focus":brief.get("recommended_focus",[]),
      "action_count":len(actions),
      "actions":actions,
      "external_authority_granted":False
    }
    save(OUT,payload);save(STATE,{"last_built_at":now(),"action_count":len(actions)})
    save(HEALTH,{"healthy":True,"last_checked_at":now(),"action_count":len(actions)})
    return {"success":True,"status":"strategic_plan_complete","plan":payload}

def status():
    return {"success":True,"status":"strategic_plan_status","state":load(STATE,{}),
      "health":load(HEALTH,{}),"plan":load(OUT,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {"success":False,"allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
