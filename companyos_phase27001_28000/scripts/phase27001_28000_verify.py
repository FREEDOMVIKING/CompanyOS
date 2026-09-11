#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.businessops import VentureEngine, RevenueTracker, PortfolioPolicy, BusinessOpsStatus

ranked = VentureEngine().select([
    {"name":"a","expected_value":100,"confidence":0.8,"risk":0.1,"effort":0.2},
    {"name":"b","expected_value":50,"confidence":0.5,"risk":0.5,"effort":0.5},
])
assert ranked[0]["name"] == "a"

root = Path(tempfile.mkdtemp())
t = RevenueTracker(root)
t.record("v", revenue=100, cost=40)
s = t.summary("v")
assert s["profit"] == 60

p = PortfolioPolicy().decide(s)
assert p["action"] == "scale"

assert BusinessOpsStatus().status()["status"] == "phase28000_autonomous_business_and_revenue_loop_ready"

print(json.dumps({
    "success": True,
    "status": "phase27001_28000_verification_passed",
    "cycle_status": "phase28000_autonomous_business_and_revenue_loop_ready"
}, indent=2))
