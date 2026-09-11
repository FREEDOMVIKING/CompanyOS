#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.enterpriseopt import *

root=Path(tempfile.mkdtemp())

score=EnterpriseScorecard().evaluate([{"venture_id":"v","growth":.8,"margin":.8,"retention":.8,"reliability":.8,"strategic_fit":.8}])
assert score[0]["enterprise_score"]>.7
assert EnterpriseCapitalAllocator().allocate(score,1000)
assert VenturePruner().decide(score)[0]["action"]=="scale"
assert DepartmentCapacityPlanner().plan([{"name":"r","demand":2,"capacity":1}])[0]["action"]=="add_capacity"
assert EnterpriseAuthorityBoundary().evaluate({"kind":"major_capital_reallocation"})["requires_approval"]
assert EnterpriseOptimizationStatus().status()["status"]=="phase11000_autonomous_enterprise_optimization_portfolio_ready"

print(json.dumps({
    "success":True,
    "status":"phase10501_11000_verification_passed",
    "cycle_status":"phase11000_autonomous_enterprise_optimization_portfolio_ready"
},indent=2))
