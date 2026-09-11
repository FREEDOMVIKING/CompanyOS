#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"phase23_executive_dashboard.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d

def build():
    payload={
      "generated_at":now(),
      "autonomy":load("autonomy_core_health.json",{}),
      "performance":load("business_performance_scorecard.json",{}),
      "opportunities":load("generated_business_opportunities.json",{}),
      "improvement_proposals":load("self_improvement_proposals.json",{}),
      "memory":load("persistent_memory_state.json",{}),
      "api_usage":load("api_usage_state.json",{}),
      "specialist_runtime":load("specialist_runtime_health.json",{}),
      "validated_insights":load("validated_insights.json",{}),
      "external_authority":{
        "external_write":False,"customer_contact":False,"publication":False,
        "spending":False,"fund_transfer":False,"code_changes":False,
        "merge":False,"deploy":False,"destructive_actions":False
      }
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return {"success":True,"status":"phase23_executive_dashboard_complete","dashboard":payload}

a=sys.argv[1] if len(sys.argv)>1 else "show"
r=build()
print(json.dumps(r,indent=2))
