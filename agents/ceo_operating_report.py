#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"ceo_operating_report.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d

def build():
    perf=load("business_performance_scorecard.json",{})
    tasks=load("persistent_task_registry.json",{})
    validated=load("validated_business_opportunities.json",{})
    collab=load("specialist_collaboration_groups.json",{})
    kpis=load("kpi_goal_tracker.json",{})
    watchdog=load("autonomy_watchdog_report.json",{})
    payload={
      "generated_at":now(),
      "headline":"CompanyOS CEO Operating Report",
      "business_performance_score":perf.get("overall_score"),
      "active_task_count":tasks.get("task_count",0),
      "validated_opportunity_count":sum(
        1 for x in validated.get("opportunities",[])
        if x.get("validation_status")=="validated_internal_candidate"
      ),
      "specialist_collaboration_group_count":collab.get("group_count",0),
      "kpi_goals":kpis.get("goals",[]),
      "system_health":"healthy" if watchdog.get("healthy",False) else "attention",
      "external_authority_granted":False
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return {"success":True,"status":"ceo_operating_report_complete","report":payload}

r=build()
print(json.dumps(r,indent=2))
