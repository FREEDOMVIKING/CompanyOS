#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.scaleops import *

root=Path(tempfile.mkdtemp())

assert FinancialPlanner().plan(1000,200,300)["operating_profit"]==500.0
assert CashflowEngine().evaluate(1000,500,300)["closing_cash"]==1200.0
assert RunwayManager().compute(1200,100)["status"]=="healthy"
assert ScaleAllocator().allocate([{"name":"x","expected_roi":2,"confidence":.8,"capacity":1}],1000)
assert ComplianceRegistry().evaluate([{"key":"privacy"}],["privacy"])["ready"]
assert RiskRegister().prioritize([{"name":"x","likelihood":.5,"impact":.8,"detectability":.5}])
assert ApprovalMatrix().route([{"kind":"bank_transfer","amount":1000}])["approval_queue"]
assert ScaleOpsStatus().status()["status"]=="phase5000_autonomous_finance_compliance_scale_ready"

print(json.dumps({
    "success":True,
    "status":"phase4501_5000_verification_passed",
    "cycle_status":"phase5000_autonomous_finance_compliance_scale_ready"
},indent=2))
