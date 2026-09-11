#!/usr/bin/env python3
import json
from companyos.venture_factory import *
r=OpportunityEngine().rank([{"name":"a","demand":.9,"pain":.8,"willingness_to_pay":.8,"competition":.2,"evidence":.9}])
assert r[0]["opportunity_score"]>.5
assert len(ExperimentEngine().plan(r[0]))==4
assert UnitEconomicsEngine().evaluate(1000,200,100,10)["profitable"]
assert PortfolioEngine().decide([{"venture_id":"v","score":.8,"growth":.3,"reliability":.9}])[0]["decision"]=="SCALE"
assert VentureGuardrails().route([{"kind":"bank_transfer"}])["approval_queue"]
assert VentureFactoryStatus().status()["status"]=="phase4000_autonomous_venture_factory_ready"
print(json.dumps({"success":True,"status":"phase3501_4000_verification_passed","cycle_status":"phase4000_autonomous_venture_factory_ready"},indent=2))
