#!/usr/bin/env python3
import json
from dataclasses import asdict

from companyos.runtime.opportunity_discovery_engine import OpportunityDiscoveryEngine
from companyos.runtime.opportunity_goal_generator import OpportunityGoalGenerator

engine = OpportunityDiscoveryEngine()

batch = engine.ingest_candidates([
    {
        "title": "Internal small-business workflow assistant",
        "description": "Research a lightweight AI-assisted workflow product for small service businesses.",
        "source": "manual_demo_seed",
        "category": "software",
        "confidence": 0.85,
        "novelty": 0.65,
        "feasibility": 0.9,
        "strategic_fit": 0.9,
        "expected_value": 0.75,
    }
])

result = OpportunityGoalGenerator(min_score=60.0).generate_best_available()

print(json.dumps(asdict(batch), indent=2))
print(json.dumps(asdict(result), indent=2))
print("PHASE106_RUNTIME_SEED_DEMO: PASS")
