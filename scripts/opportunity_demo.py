#!/usr/bin/env python3
import json
from companyos_phase293_300 import OpportunityPipeline

sample = [{
    "name": "Contractor Bid Copilot",
    "problem": "Small contractors lose time turning scope into fast professional estimates.",
    "customer": "Small construction contractors",
    "solution": "AI-assisted estimating and proposal workflow",
    "revenue_model": "monthly SaaS",
    "evidence": ["repetitive workflow", "high labor cost of estimating"],
    "metrics": {
        "demand": 8,
        "speed_to_revenue": 8,
        "margin": 9,
        "automation": 9,
        "competition_advantage": 6,
        "recurring_revenue": 9,
        "capital_efficiency": 9,
    },
}]
print(json.dumps(OpportunityPipeline().rank(sample), indent=2))
