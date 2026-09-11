#!/usr/bin/env python3
import json
from companyos_phase385_400 import CEOValidationBridge

thesis = {
    "name": "Workflow Automation Copilot",
    "customer": "small and mid-sized businesses",
    "core_problem": "Repeated manual workflow pain",
    "business_model": {"primary":"monthly SaaS subscription"},
}

bridge = CEOValidationBridge()
plan = bridge.prepare(thesis)
print("=== VALIDATION PLAN ===")
print(json.dumps(plan, indent=2))

sample_metrics = {
    "landing_page_visits": 150,
    "email_conversion": 0.11,
    "interview_count": 7,
    "pain_confirm_rate": 0.71,
    "willingness_to_pay_confirm_rate": 0.43,
    "qualified_leads": 8,
}

print("\n=== SAMPLE EVALUATION ===")
print(json.dumps(bridge.evaluate(thesis, sample_metrics), indent=2))
