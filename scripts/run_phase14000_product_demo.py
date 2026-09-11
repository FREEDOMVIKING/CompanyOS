#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.productops import CEOProductOpsController

r=CEOProductOpsController(Path.home()/"companyos").run(
    problem_signals=[
        {"name":"slow_estimating","pain":.95,"frequency":.9,"urgency":.85,"willingness_to_pay":.8},
        {"name":"manual_reporting","pain":.7,"frequency":.8,"urgency":.6,"willingness_to_pay":.65}
    ],
    initiatives=[
        {"name":"auto_estimate","customer_value":.95,"strategic_fit":.95,"evidence":.85,"effort":1,"risk":.2},
        {"name":"reporting_v2","customer_value":.75,"strategic_fit":.8,"evidence":.7,"effort":.8,"risk":.15}
    ],
    features=[
        {"name":"one_click_estimate","reach":.9,"impact":.95,"confidence":.8,"effort":1},
        {"name":"custom_dashboard","reach":.7,"impact":.7,"confidence":.75,"effort":1.2}
    ],
    concept={"name":"AI estimating copilot"},
    experiments=[{"name":"prototype_test","result":.82,"success_threshold":.7}],
    release={"environment":"staging","artifact":"estimate_v1"},
    quality_signals={
        "tests_passed":True,"security_passed":True,"performance_passed":True,
        "rollback_ready":True,"observability_ready":True
    },
    cohorts=[{"name":"pilot","activation":.8,"engagement":.75,"retention":.8}],
    product_metrics={"activation_rate":.8,"feature_adoption":.72,"retention_rate":.82,"nps_proxy":.85},
    innovation_bets=[
        {"name":"voice_estimating","upside":.8,"confidence":.6,"strategic_value":.9,"risk":.3},
        {"name":"regional_cost_model","upside":.9,"confidence":.8,"strategic_value":.95,"risk":.2}
    ],
    innovation_budget=5000,
    actions=[
        {"kind":"internal_prototype"},
        {"kind":"production_deploy"},
        {"kind":"public_launch"},
        {"kind":"collect_new_sensitive_data"}
    ]
)

print(json.dumps(r,indent=2,default=str))
