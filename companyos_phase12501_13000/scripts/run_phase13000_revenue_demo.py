#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.revenueops import CEORevenueOpsController
r=CEORevenueOpsController(Path.home()/"companyos").run(
 signals=[{"name":"construction_estimating","demand":.9,"urgency":.8,"willingness_to_pay":.8,"fit":.95}],
 offers=[{"name":"AI Estimating Pro","value_score":.9,"friction":.2,"proof":.75,"margin":.8}],
 base_price=199,
 leads=[{"stage":"qualified","expected_value":2400,"probability":.6},{"stage":"proposal","expected_value":5000,"probability":.75}],
 customers=[{"customer_id":"c1","health":.9,"usage_growth":.2,"revenue":2400,"retention_probability":.9},{"customer_id":"c2","health":.35,"usage_growth":-.1,"revenue":1200,"retention_probability":.5}],
 economics={"revenue":199,"variable_cost":35,"acquisition_cost":120,"retention_months":18},
 current_mrr=10000,growth_rate=.08,
 channels=[{"name":"outbound","roi":3,"confidence":.8,"risk":.2},{"name":"content","roi":4,"confidence":.65,"risk":.15}],
 growth_budget=5000,
 experiments=[{"name":"pricing_test","impact":.8,"confidence":.75,"effort":1},{"name":"onboarding_test","impact":.7,"confidence":.85,"effort":.7}],
 actions=[{"kind":"internal_pricing_analysis"},{"kind":"charge_customer"},{"kind":"large_ad_spend"}]
)
print(json.dumps(r,indent=2,default=str))
