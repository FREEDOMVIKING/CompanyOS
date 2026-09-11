#!/usr/bin/env python3
import json
from companyos_phase609_624 import CEODeliveryBridge

packet = {
    "success":True,
    "venture_id":"venture_demo",
    "brief":{
        "product_name":"Contractor Bid Copilot",
        "target_customer":"small contractors",
        "problem":"slow estimating and proposal workflow",
    },
    "mvp_scope":{
        "must_have":["core estimating workflow","proposal output","telemetry"],
        "defer":["enterprise admin"],
    },
    "quality_gates":["targeted_tests_pass","regression_tests_pass"],
    "kpis":{"activation":["activation_rate"],"revenue":["trial_to_paid"]},
}

bridge = CEODeliveryBridge()
print("=== DELIVERY PACKET ===")
print(json.dumps(bridge.prepare(packet), indent=2))

build_result = {
    "artifacts":["app.py","tests/test_app.py","README.md"],
    "core_workflow_verified":True,
    "tests_passed":True,
    "documentation_present":True,
}
qa = {
    "targeted_tests_pass":True,
    "regression_tests_pass":True,
    "no_known_critical_defects":True,
    "core_workflow_verified":True,
    "telemetry_verified":True,
    "rollback_ready":True,
    "telemetry_ready":True,
    "secrets_configured_safely":True,
    "support_path_ready":True,
}

print("\n=== DELIVERY REVIEW ===")
print(json.dumps(bridge.review_build("venture_demo", build_result, qa), indent=2))
