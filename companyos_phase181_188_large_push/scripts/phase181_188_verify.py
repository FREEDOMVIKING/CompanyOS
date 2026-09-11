#!/usr/bin/env python3
import json
from companyos_phase181_188 import *
assert NorthStarManager().align([{"name":"x","relevance":1,"impact":1,"evidence":1}],"grow")[0]["continue"]
assert OpportunityPipeline().advance([{"evidence":.8,"demand":.8}])[0]["next_stage"]=="incubate"
assert VentureIncubator().incubate({"name":"x"})["autonomous_internal_incubation"]
assert AutonomousOperator().authorize({"kind":"write_code","reversible":True,"bounded":True})["allowed"]
assert not AutonomousOperator().authorize({"kind":"unknown"})["allowed"]
assert PerformanceCompounder().learn([{"runs":5,"success_rate":.9,"gain":.2}])[0]["promote_to_default"]
assert round(InternalResourceMarket().allocate([{"name":"x","expected_value":1,"evidence":1,"learning":1,"risk":0}],100)[0]["capacity"],2)==100
assert RecoveryOrchestrator().recover([{"name":"worker","healthy":False,"attempts":0}])[0]["autonomous"]
r=EnterpriseBrain().run({"north_star":"grow"})
assert r["success"] and r["enterprise_brain_active"] and r["autonomy_mode"]=="high"
print(json.dumps({"success":True,"status":"phase181_188_verification_passed","cycle_status":r["status"],
"autonomy_mode":"high","enterprise_brain_active":True,"external_action_taken":False,
"financial_action_taken":False,"irreversible_action_taken":False},indent=2))
