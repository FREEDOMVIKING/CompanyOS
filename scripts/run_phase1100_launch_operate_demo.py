#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase1001_1100 import CEOLaunchOperateController

root=Path.home()/"companyos"

result=CEOLaunchOperateController(root).run(
    venture_id="demo_venture",
    release_candidate={"passed":True,"status":"release_candidate_ready"},
    artifact_path=None,
    environment="staging",
    launch_metrics={"error_rate":0.01,"availability":0.999,"p95_latency_ms":420},
    customer_feedback=[
        {"theme":"onboarding","severity":"high"},
        {"theme":"pricing","severity":"medium","revenue_impact":True},
        {"theme":"onboarding","severity":"low"},
    ],
    revenue_inputs={"revenue":1250,"customers":25,"spend":300,"refunds":50},
    growth_metrics={"activation_rate":0.68,"retention_rate":0.52,"conversion_rate":0.08,"growth_rate":0.18},
    business_risk_metrics={"refund_rate":0.04,"chargeback_rate":0.01},
)

print(json.dumps(result,indent=2,default=str))
