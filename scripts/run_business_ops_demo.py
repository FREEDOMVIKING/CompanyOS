#!/usr/bin/env python3
import json
from companyos_phase449_464 import CEOOperationsBridge

bridge = CEOOperationsBridge()

launch = bridge.launch_review({
    "release_candidate_ready":True,
    "telemetry_ready":True,
    "rollback_ready":True,
    "support_path_ready":True,
})

metrics = {
    "qualified_visitors":1000,
    "leads":140,
    "activated_users":80,
    "paying_customers":12,
    "customers_start":12,
    "customers_end":10,
    "customers_churned":2,
    "mrr":1200,
    "previous_mrr":900,
    "cac":60,
    "arpa":100,
    "gross_margin":0.8,
    "monthly_churn":0.08,
    "sample_size":80,
}

print("=== LAUNCH READINESS ===")
print(json.dumps(launch, indent=2))
print("\n=== OPERATING REVIEW ===")
print(json.dumps(bridge.operating_review(metrics), indent=2))
