#!/usr/bin/env python3
import json
from companyos_phase385_400 import (
    HypothesisBuilder, ValidationBudget, ExperimentDesigner, LandingPageSpec,
    OfferBuilder, PricingTest, DemandThresholds, ResultInterpreter,
    GoNoGoEngine, ValidationScorecard, ValidationOrchestrator,
    CEOValidationBridge, ValidationRuntime
)

thesis = {
    "name":"Test Opportunity",
    "customer":"small businesses",
    "core_problem":"manual workflow is slow",
    "business_model":{"primary":"monthly SaaS subscription"},
}

assert HypothesisBuilder().build(thesis)["customer_hypothesis"]
assert ValidationBudget().limits()["max_experiments_per_opportunity"] >= 1
assert ExperimentDesigner().design(thesis)
assert LandingPageSpec().build(thesis)["purpose"] == "validation_only"
assert OfferBuilder().build(thesis)["requires_full_product"] is False
assert PricingTest().create(thesis)["automatic_charging"] is False
thresholds = DemandThresholds().defaults()

metrics = {
    "landing_page_visits": 120,
    "email_conversion": 0.1,
    "interview_count": 6,
    "pain_confirm_rate": 0.7,
    "willingness_to_pay_confirm_rate": 0.4,
    "qualified_leads": 7,
}
interp = ResultInterpreter().interpret(metrics, thresholds)
assert interp["pass_ratio"] == 1.0
decision = GoNoGoEngine().decide(interp)
assert decision["decision"] == "go_to_mvp"
assert ValidationScorecard().build(thesis, interp, decision)
assert ValidationOrchestrator().plan(thesis)["full_product_build_required"] is False
assert CEOValidationBridge().evaluate(thesis, metrics)["success"] is True
assert ValidationRuntime().status()["success"] is True

print(json.dumps({
    "success": True,
    "status": "phase385_400_verification_passed",
    "cycle_status": "phase400_validation_experiment_engine_ready",
    "hypothesis_engine": True,
    "bounded_validation_budget": True,
    "experiment_design": True,
    "landing_page_specs": True,
    "offer_and_pricing_tests": True,
    "demand_thresholds": True,
    "go_nogo_engine": True,
    "validation_scorecard": True,
    "ceo_validation_bridge": True,
    "autonomy_mode": "high"
}, indent=2))
