#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
OUT=MEM/"executive_briefing.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(name,d):
    try:return json.loads((MEM/name).read_text(encoding="utf-8"))
    except:return d

def build():
    performance=load("business_performance_scorecard.json",{})
    opportunities=load("generated_business_opportunities.json",{}).get("opportunities",[])
    improvements=load("governed_improvement_queue.json",{}).get("items",[])
    provider=load("provider_health_report.json",{})
    specialists=load("specialist_performance_profiles.json",{}).get("profiles",[])
    autonomy=load("autonomy_core_health.json",{})

    payload={
      "generated_at":now(),
      "headline":"CompanyOS Executive Briefing",
      "system_health":"healthy" if autonomy.get("healthy",False) else "attention",
      "business_performance_score":performance.get("overall_score"),
      "top_opportunities":opportunities[:5],
      "top_improvement_items":improvements[:5],
      "provider_health":provider,
      "top_specialist_profiles":specialists[:5],
      "recommended_focus":[
        x.get("title") for x in opportunities[:3] if x.get("title")
      ],
      "external_authority_granted":False
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return {"success":True,"status":"executive_briefing_complete","briefing":payload}

r=build()
print(json.dumps(r,indent=2))
