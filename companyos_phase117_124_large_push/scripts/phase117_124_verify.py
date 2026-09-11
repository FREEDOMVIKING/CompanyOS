#!/usr/bin/env python3
import json
from companyos_phase117_124 import *
assert HypothesisManager().rank([{"name":"x","impact":1,"confidence":1,"ease":1}])[0]["name"]=="x"
assert MarketModel().estimate(100,1000,.5,.1)["som"]==5000
assert ProductPortfolio().review([{"name":"x","traction":1,"margin":1,"fit":1,"risk":0}])[0]["recommendation"]=="invest"
assert CustomerSuccess().analyze([{"usage":1,"satisfaction":1,"trend":1}])[0]["status"]=="healthy"
assert CashflowPlanner().project(100,[50],[25])["funds_moved"] is False
assert ComplianceGate().evaluate({"category":"legal_commitment"})["allowed"] is False
assert ComplianceGate().evaluate({"category":"legal_commitment","compliance_reviewed":True})["allowed"] is True
assert AutonomyBudget().check(5,10,4)["allowed"] is True
c=CompanyOperatingSystem().run({"hypotheses":[{"name":"offer","impact":.9,"confidence":.7,"ease":.8}],
"total_customers":1000,"annual_value":1200,"serviceable_pct":.5,"obtainable_pct":.1,
"products":[{"name":"p","traction":.8,"margin":.8,"fit":.8,"risk":.2}],
"starting_cash":1000,"monthly_inflows":[100],"monthly_outflows":[50],
"autonomy_used":1,"autonomy_limit":10,"autonomy_requested":2})
assert c["success"] and not c["external_action_taken"] and not c["financial_action_taken"] and not c["irreversible_action_taken"]
print(json.dumps({"success":True,"status":"phase117_124_verification_passed","cycle_status":c["status"],
"external_action_taken":c["external_action_taken"],"financial_action_taken":c["financial_action_taken"],
"irreversible_action_taken":c["irreversible_action_taken"]},indent=2))
