#!/usr/bin/env python3
import json
from companyos_phase77_84 import *
assert CustomerEngine().segment([{"segment":"smb","pain":.9,"willingness":.8}])[0]["segment"]=="smb"
assert SalesPipeline().forecast([{"value":100,"stage":"won"}])["weighted_forecast"]==100
assert FinanceController().assess(1000,100,50)["funds_moved"] is False
assert ExecutionScheduler().ready([{"id":"x","priority":1,"depends_on":[]}])[0]["id"]=="x"
assert CompetitiveIntelligence().gaps(["a"],[{"features":["a","b"]}])["missing_common_features"][0]["feature"]=="b"
assert ScaleEngine().evaluate({"growth":.9,"retention":.9,"margin":.9,"reliability":.9})["automatic_external_scaling"] is False
assert ResilienceManager().plan({"kind":"timeout","attempts":1})["retry"] is True
c=CompanyOrchestrator().run({"cash":1000,"monthly_burn":100,"planned_spend":0,
"customer_signals":[{"segment":"smb","pain":.8,"willingness":.7}],
"deals":[{"value":100,"stage":"qualified"}],"tasks":[{"id":"t","priority":10,"depends_on":[]}],
"kpis":{"growth":.8,"retention":.8,"margin":.8,"reliability":.8}})
assert c["success"] and not c["external_action_taken"]
print(json.dumps({"success":True,"status":"phase77_84_verification_passed",
"cycle_status":c["status"],"external_action_taken":c["external_action_taken"]},indent=2))
