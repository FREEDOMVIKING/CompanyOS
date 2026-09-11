#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.finalops import *

root=Path(tempfile.mkdtemp())
assert IntegrationValidator().validate([{"source":"a","target":"b","contract":"x"}])["valid"]
assert EndToEndRunner().run(["discover","research","validate","build","launch","operate","optimize","portfolio_review"])["passed"]
assert RegressionMatrix().evaluate([{"name":"x","passed":True}])["passed"]
assert ContinuityChecker().evaluate({"x":1},{"q":1},{"m":1})["continuous"]
assert RecoveryValidator().validate([{"expected":"resume","actual":"resume"}])["passed"]
assert ApprovalBoundaryValidator().validate([{"kind":"contract_signature","requires_approval":True}])["passed"]
assert FinalOpsStatus().status()["status"]=="phase7000_final_integration_validation_ready"
print(json.dumps({"success":True,"status":"phase6501_7000_verification_passed",
"cycle_status":"phase7000_final_integration_validation_ready"},indent=2))
