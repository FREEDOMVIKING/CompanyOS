#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"ceo_project_portfolio.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d

def build():
    projects=load("project_execution_registry.json",{}).get("projects",[])
    teams=load("specialist_project_teams.json",{}).get("teams",[])
    incubation=load("business_incubation_portfolio.json",{}).get("candidates",[])
    milestones=load("project_milestones.json",{}).get("projects",[])
    budgets=load("project_resource_budgets.json",{}).get("allocations",[])
    replans=load("replan_recovery_actions.json",{})
    payload={
      "generated_at":now(),
      "project_count":len(projects),
      "projects":projects,
      "team_count":len(teams),
      "incubation_candidate_count":len(incubation),
      "milestone_project_count":len(milestones),
      "resource_budget_count":len(budgets),
      "replan_failure_count":replans.get("failure_count",0),
      "external_authority_granted":False
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return {"success":True,"status":"ceo_project_portfolio_complete","portfolio":payload}

r=build()
print(json.dumps(r,indent=2))
