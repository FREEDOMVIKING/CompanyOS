#!/usr/bin/env python3
import json
from companyos_phase293_300 import (
    CycleFlatteningPolicy, ProgressReporter, OpportunitySchema,
    OpportunityScoring, OpportunityPipeline, BusinessThesis,
    ValidationPlan, OpportunityRuntime,
)

assert CycleFlatteningPolicy().supervisor_limits_for_rounds(3)["total_expected_cycles"] == 3
assert ProgressReporter().event("x")["stage"] == "x"

schema = OpportunitySchema().normalize({
    "name":"x","problem":"p","customer":"c","solution":"s","revenue_model":"r","evidence":["e"]
})
assert schema["valid"] is True

score = OpportunityScoring().score({
    "demand":10,"speed_to_revenue":10,"margin":10,"automation":10,
    "competition_advantage":10,"recurring_revenue":10,"capital_efficiency":10
})
assert score == 10.0

ranked = OpportunityPipeline().rank([{
    "name":"x","problem":"p","customer":"c","solution":"s",
    "revenue_model":"r","evidence":["e"],"metrics":{"demand":8}
}])
assert ranked[0]["valid"] is True
assert ranked[0]["validation_plan"]["build_full_product_before_validation"] is False
assert BusinessThesis().default()["favor"]
assert ValidationPlan().create({"name":"x"})["steps"]
assert OpportunityRuntime().status()["success"] is True

print(json.dumps({
    "success": True,
    "status": "phase293_300_verification_passed",
    "cycle_status": "phase300_opportunity_intelligence_foundation_ready",
    "nested_cycle_fix_ready": True,
    "progress_reporting": True,
    "opportunity_schema": True,
    "economic_scoring": True,
    "validation_before_build": True,
    "business_thesis": True,
    "autonomy_mode": "high"
}, indent=2))
