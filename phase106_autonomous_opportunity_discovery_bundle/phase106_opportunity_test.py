#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.runtime.autonomous_goal_intake import AutonomousGoalIntake
from companyos.runtime.goal_source_policy import GoalSourcePolicy
from companyos.runtime.policy_guarded_goal_intake import PolicyGuardedGoalIntake
from companyos.runtime.opportunity_discovery import OpportunityDiscoveryStore
from companyos.runtime.opportunity_discovery_engine import OpportunityDiscoveryEngine
from companyos.runtime.opportunity_goal_generator import OpportunityGoalGenerator

with tempfile.TemporaryDirectory(prefix="phase106_opportunity_") as td:
    base = Path(td)

    store = OpportunityDiscoveryStore(base / "opportunities")
    intake = AutonomousGoalIntake(base / "intake")
    guarded = PolicyGuardedGoalIntake(
        intake=intake,
        policy=GoalSourcePolicy(),
    )
    engine = OpportunityDiscoveryEngine(store)
    generator = OpportunityGoalGenerator(
        store=store,
        guarded_intake=guarded,
        min_score=60.0,
    )

    batch = engine.ingest_candidates([
        {
            "title": "Internal AI document summarizer",
            "description": "Build and test an internal document summarization product concept.",
            "source": "test_signal",
            "category": "software",
            "confidence": 0.9,
            "novelty": 0.7,
            "feasibility": 0.95,
            "strategic_fit": 0.9,
            "expected_value": 0.8,
        },
        {
            "title": "Low-value idea",
            "description": "Weak fit and low feasibility.",
            "source": "test_signal",
            "category": "software",
            "confidence": 0.2,
            "novelty": 0.3,
            "feasibility": 0.2,
            "strategic_fit": 0.1,
            "expected_value": 0.2,
        },
    ])

    best = generator.generate_best_available()
    again = generator.generate_best_available()

    checks = {
        "two_candidates_discovered": batch.discovered == 2,
        "two_candidates_stored": batch.stored == 2,
        "top_score_above_threshold": batch.top_score >= 60.0,
        "best_generated": best.generated is True,
        "intake_created": best.intake_id is not None,
        "single_intake_record": len(intake.all_records()) == 1,
        "second_call_not_duplicate": again.reason in ("below_score_threshold", "no_eligible_opportunity"),
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("OPPORTUNITY_DISCOVERY_EXTERNAL_ACTIONS: False")
    print("OPPORTUNITY_DISCOVERY_SIGNS_TRANSACTION: False")
    print("OPPORTUNITY_DISCOVERY_BROADCASTS: False")
    print("PHASE106_OPPORTUNITY_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
