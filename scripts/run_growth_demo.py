#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase625_640 import CEOGrowthBridge

root=Path.home()/"companyos"
bridge=CEOGrowthBridge(root)

venture={
    "venture_id":"venture_demo",
    "brief":{
        "product_name":"Contractor Bid Copilot",
        "target_customer":"small contractors",
        "problem":"slow estimating and proposal workflow",
        "value_proposition":"create accurate bids faster",
    }
}
channels=[
    {"name":"direct_outreach","audience_fit":8,"commercial_intent":8,"estimated_cost":1},
    {"name":"search_content","audience_fit":7,"commercial_intent":6,"estimated_cost":2},
]
print(json.dumps(bridge.plan(venture,channels),indent=2))

metrics={
    "qualified_visitors":100,
    "qualified_leads":20,
    "activated_users":12,
    "paying_customers":5,
    "retained_customers":4,
    "revenue":500,
    "acquisition_spend":100,
    "average_revenue_per_account":100,
    "gross_margin_rate":0.8,
    "monthly_churn_rate":0.08,
}
print(json.dumps(bridge.evaluate("venture_demo",metrics),indent=2))
