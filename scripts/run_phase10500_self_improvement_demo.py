#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.selfimprove import CEOSelfImprovementController

result=CEOSelfImprovementController(Path.home()/"companyos").run(
    metrics={
        "latency":6.5,
        "success_rate":.93,
        "cost_per_cycle":12,
        "recovery_rate":.85,
        "throughput":8
    },
    thresholds={
        "max_latency":5,
        "min_success_rate":.95,
        "max_cost_per_cycle":10,
        "min_recovery_rate":.9
    },
    patch_requests=[
        {"component":"provider_router","change":"prefer healthier lower-latency providers","reversible":True},
        {"component":"retry_policy","change":"adaptive exponential backoff","reversible":True}
    ],
    tests=[{"name":"unit","passed":True},{"name":"integration","passed":True}],
    candidate_metrics={
        "latency":4.8,
        "success_rate":.97,
        "cost_per_cycle":9,
        "recovery_rate":.93,
        "throughput":10
    },
    events=[
        {"kind":"provider_failure"},
        {"kind":"provider_failure"},
        {"kind":"customer_signal"},
        {"kind":"revenue_signal"}
    ],
    current_strategy={"revision":3,"focus":"profitable_safe_growth"},
    modules=[
        {"name":"router_a","role":"provider_routing"},
        {"name":"router_b","role":"provider_routing"},
        {"name":"health","role":"health_monitoring"}
    ],
    changes=[
        {"kind":"internal_strategy"},
        {"kind":"safety_policy"},
        {"kind":"financial_authority"}
    ]
)

print(json.dumps(result,indent=2,default=str))
