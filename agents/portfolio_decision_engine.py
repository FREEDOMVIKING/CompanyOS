#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
REVIEWS=MEM/"executive_review_queue.json"
RISKS=MEM/"enterprise_risk_register.json"
BUDGETS=MEM/"project_resource_budgets.json"
OUT=MEM/"portfolio_decision_board.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d

def build():
    reviews=load("executive_review_queue.json",{}).get("reviews",[])
    risks=load("enterprise_risk_register.json",{}).get("risks",[])
    budgets=load("project_resource_budgets.json",{}).get("allocations",[])
    payload={
      "generated_at":now(),
      "review_count":len(reviews),
      "risk_count":len(risks),
      "resource_allocation_count":len(budgets),
      "recommended_portfolio_actions":[
        "Continue internal validation for high-scoring projects",
        "Prioritize projects with measurable outcome commitments",
        "Escalate any external action to explicit approval",
        "Pause or re-plan projects with unresolved material risk"
      ],
      "external_authority_granted":False
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return {"success":True,"status":"portfolio_decision_board_complete","board":payload}

r=build()
print(json.dumps(r,indent=2))
