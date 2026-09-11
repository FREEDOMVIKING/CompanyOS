#!/usr/bin/env python3
import json
from companyos.ceofinops import FinancialPlanner, ExpectedValueEngine, CapitalAllocator, CEOFinOpsStatus

p = FinancialPlanner().build_plan({
    "name":"x",
    "required_capital":10,
    "expected_return":30,
    "confidence":0.8,
    "risk":0.1
})
assert p["required_capital"] == 10

e = ExpectedValueEngine().evaluate(p)
assert e["positive_ev"] is True

alloc = CapitalAllocator().allocate(
    [{"plan":p,"evaluation":e}],
    available_capital=1000,
    reserve_floor=250
)
assert alloc["allocations"][0]["allocated_capital"] == 10

s = CEOFinOpsStatus().status()
assert s["hard_treasury_limits_external_to_ai"] is True
assert s["live_execution_auto_enabled"] is False

print(json.dumps({
    "success":True,
    "status":"phase26001_27000_verification_passed",
    "cycle_status":"phase27000_ceo_financial_decision_loop_ready",
    "live_execution_auto_enabled":False
}, indent=2))
