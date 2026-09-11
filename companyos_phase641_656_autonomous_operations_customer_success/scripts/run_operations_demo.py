#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase641_656 import CEOOperationsBridge

bridge=CEOOperationsBridge(Path.home()/"companyos")

customer={
    "usage_score":0.35,
    "value_realization":0.45,
    "satisfaction_score":0.4,
    "open_critical_issues":1,
    "usage_change_30d":-0.5,
    "unresolved_tickets":3,
}
print("=== CUSTOMER REVIEW ===")
print(json.dumps(bridge.review_customer(customer),indent=2))

state={
    "tickets":[
        {"id":"t1","severity":"critical","blocks_core_value":True},
        {"id":"t2","severity":"medium"},
    ],
    "service_metrics":{"uptime":0.995,"error_rate":0.01,"core_workflow_success_rate":0.97},
    "customer_success_metrics":{
        "customers_start":10,"customers_retained":9,
        "starting_recurring_revenue":1000,"churned_revenue":50,
        "expansion_revenue":100,"support_csat":4.5,"time_to_value_hours":2,
    },
    "support_backlog":25,
    "critical_incidents":0,
    "churn_rate":0.05,
    "activation_rate":0.3,
}
print("=== BUSINESS OPERATIONS REVIEW ===")
print(json.dumps(bridge.review_business(state),indent=2))
