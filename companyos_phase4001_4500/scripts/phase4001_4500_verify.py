#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.marketops import *

root=Path(tempfile.mkdtemp())

assert MarketSignalEngine().score([{"demand":1,"pain":1,"urgency":1,"budget":1,"competition_gap":1,"evidence_quality":1}])[0]["market_score"]>.9
assert CustomerDiscoveryEngine().segment([{"segment":"a","pain":1,"budget_signal":1,"urgency":1}])[0]["segment"]=="a"
assert ChannelOptimizer().rank([{"name":"x","cac":10,"ltv":100,"conversion_rate":.1,"scalability":.8,"lead_quality":.9}])[0]["channel_score"]>0
assert PricingEngine().recommend([{"name":"pro","price":100,"conversion_rate":.1,"retention_rate":.8,"gross_margin":.8}])["winner"]["name"]=="pro"
assert SalesOrchestrator().next_actions([{"pain_confirmed":True,"budget_confirmed":True}])[0]["lead_score"]>=50
assert MarketOpsGuardrails().route([{"kind":"contract_signature"}])["approval_queue"]
assert MarketOpsStatus().status()["status"]=="phase4500_autonomous_market_execution_growth_ready"

print(json.dumps({
    "success":True,
    "status":"phase4001_4500_verification_passed",
    "cycle_status":"phase4500_autonomous_market_execution_growth_ready"
},indent=2))
