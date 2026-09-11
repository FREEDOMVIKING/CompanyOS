#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"executive_action_board.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d

def build():
    strategic=load("strategic_30_day_plan.json",{}).get("actions",[])
    research=load("research_mission_queue.json",{}).get("missions",[])
    goals=load("kpi_goal_tracker.json",{}).get("goals",[])
    improvements=load("governed_improvement_queue.json",{}).get("items",[])
    resources=load("portfolio_resource_plan.json",{}).get("allocations",[])
    payload={
      "generated_at":now(),
      "top_strategic_actions":strategic[:10],
      "research_missions":research[:10],
      "kpi_goals":goals,
      "improvement_queue":improvements[:10],
      "resource_plan":resources[:10],
      "external_authority_granted":False
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return {"success":True,"status":"executive_action_board_complete","board":payload}

r=build()
print(json.dumps(r,indent=2))
