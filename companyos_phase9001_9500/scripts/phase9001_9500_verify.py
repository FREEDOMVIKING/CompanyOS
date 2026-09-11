#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.actiongov import *

root=Path(tempfile.mkdtemp())

assert ActionPolicyEngine().evaluate({"kind":"bank_transfer"})["requires_approval"]
assert ActionRiskScorer().score({"kind":"contract_signature","external":True,"reversible":False})["risk_score"]>0
assert BudgetEnforcer().evaluate({"amount":100},1000)["allowed"]
assert ActionRateLimiter().evaluate(1,10)["allowed"]
assert DryRunEngine().simulate({"kind":"x"})["simulated"]
assert RollbackExecutor().plan({"reversible":True})["ready"]
q=PersistentApprovalQueue(root)
item=q.submit({"kind":"production_deploy"})
assert q.pending()
assert ActionGovernanceStatus().status()["status"]=="phase9500_autonomous_external_action_governance_ready"

print(json.dumps({
 "success":True,
 "status":"phase9001_9500_verification_passed",
 "cycle_status":"phase9500_autonomous_external_action_governance_ready"
},indent=2))
