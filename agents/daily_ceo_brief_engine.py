#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"; OUT=MEM/"daily_ceo_brief.json"
def now():return datetime.now(timezone.utc).isoformat()
def load(n,d):
    try:return json.loads((MEM/n).read_text())
    except:return d
def run():
    payload={
      "generated_at":now(),
      "headline":"CompanyOS Daily CEO Brief",
      "business_performance":load("business_performance_scorecard.json",{}).get("overall_score"),
      "top_market_signals":load("market_intelligence_report.json",{}).get("signals",[])[:5],
      "top_customer_priorities":load("customer_pipeline_priorities.json",{}).get("priorities",[])[:5],
      "proposal_draft_count":load("proposal_draft_queue.json",{}).get("draft_count",0),
      "execution_readiness":load("execution_readiness_report.json",{}).get("projects",[])[:10],
      "risk_count":load("enterprise_risk_register.json",{}).get("risk_count",0),
      "pending_approval_count":sum(1 for x in load("governed_approval_queue.json",{}).get("items",[]) if x.get("status")=="pending"),
      "external_authority_granted":False
    }
    OUT.write_text(json.dumps(payload,indent=2))
    return {"success":True,"status":"daily_ceo_brief_complete","brief":payload}
print(json.dumps(run(),indent=2))
