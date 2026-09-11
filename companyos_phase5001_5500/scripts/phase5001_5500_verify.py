#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.growthops import *
root=Path(tempfile.mkdtemp())
assert MarketRadar().scan([{"demand":1,"growth":1,"urgency":1,"competition":0}])[0]["market_score"]==1
assert OpportunityRanker().rank([{"value":1,"confidence":1,"speed":1,"effort":1,"risk":0}])[0]["priority_score"]==1
assert ExperimentEngine().decide([{"confidence":.8,"impact":.8,"result":.2}])[0]["action"]=="scale"
assert GrowthApprovalRouter().route([{"kind":"large_marketing_spend","amount":1000}])["approval_queue"]
assert GrowthOpsStatus().status()["status"]=="phase5500_autonomous_market_intelligence_growth_ready"
print(json.dumps({"success":True,"status":"phase5001_5500_verification_passed",
"cycle_status":"phase5500_autonomous_market_intelligence_growth_ready"},indent=2))
