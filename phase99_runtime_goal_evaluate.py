#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict

from companyos.runtime.goal_outcome_evaluator import GoalOutcomeEvaluator

ap = argparse.ArgumentParser()
ap.add_argument("goal_id")
ap.add_argument("--goal", default="")
args = ap.parse_args()

result = GoalOutcomeEvaluator().evaluate(
    goal_id=args.goal_id,
    goal=args.goal,
)

print(json.dumps(asdict(result), indent=2))
print("PHASE99_RUNTIME_GOAL_EVALUATE: PASS")
