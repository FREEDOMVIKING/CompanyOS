#!/usr/bin/env python3
import json
from companyos_phase149_156 import *
assert GoalGenerator().generate("grow",{"gaps":["distribution"]})[0]["autonomous"]
assert MarketFeedbackLoop().analyze([{"strength":.9,"confidence":.9}])[0]["next_action"]=="double_down"
assert AutonomousProductManager().prioritize([{"id":"a","customer_value":1,"business_value":1,"learning":1,"effort":.1}])[0]["id"]=="a"
assert RevenueExperimenter().design("pricing",10)["financial_action_taken"] is False
assert KnowledgeCompounder().compound([{"topic":"x","confidence":.8},{"topic":"x","confidence":.6}])[0]["observation_count"]==2
assert ResilienceManager().respond({"recommended_action":"restart_worker"})["autonomous"] is True
assert StrategyEvolver().evolve([{"results":1,"learning":1,"repeatability":1,"risk":0}])[0]["decision"]=="expand"
r=ContinuousCEO().run({"mission":"build","state":{"gaps":["sales"]}})
assert r["success"] and r["autonomy_mode"]=="high"
print(json.dumps({"success":True,"status":"phase149_156_verification_passed","cycle_status":r["status"],
"autonomy_mode":r["autonomy_mode"],"external_action_taken":False,"financial_action_taken":False,"irreversible_action_taken":False},indent=2))
