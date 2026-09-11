#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.governanceops import *

root=Path(tempfile.mkdtemp())
reg=PolicyRegistry().compile([{"policy_id":"p1","name":"Audit"}])
assert "p1" in reg
matrix=ComplianceMatrix().map([{"requirement":"r","required_controls":["audit"]}],["audit"])
assert matrix[0]["compliant"]
assert AccessReviewEngine().review([{"identity":"a","admin":True,"mfa":False}])["passed"] is False
assert GovernanceAuthorityBoundary().evaluate({"kind":"disable_audit"})["requires_approval"]
assert GovernanceOpsStatus().status()["status"]=="phase12500_autonomous_governance_compliance_command_ready"

print(json.dumps({
    "success":True,
    "status":"phase12001_12500_verification_passed",
    "cycle_status":"phase12500_autonomous_governance_compliance_command_ready"
},indent=2))
