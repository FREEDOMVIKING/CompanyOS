#!/usr/bin/env python3
import json
from companyos_phase561_576 import CEOExecutionBridge

venture={
    "venture_id":"venture_demo",
    "name":"Contractor Bid Copilot",
    "stage":"validation",
    "brief":{
        "product_name":"Contractor Bid Copilot",
        "target_customer":"small contractors",
        "problem":"slow estimating and proposal workflow",
        "business_model":{"primary":"SaaS"},
    },
}
evidence={
    "problem_signal":True,
    "source_diversity":True,
    "validation_decision":"go_to_mvp",
    "validation_score":7.5,
    "activation_rate":0.28,
    "retention_rate":0.32,
    "revenue_signal":3.5,
    "critical_issues":0,
}
print(json.dumps(CEOExecutionBridge().venture_review(venture,evidence),indent=2))
