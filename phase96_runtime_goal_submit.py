#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict

from companyos.runtime.ceo_goal_decomposer import CEOGoalDecomposer

ap = argparse.ArgumentParser()
ap.add_argument("goal")
ap.add_argument("--priority-base", type=int, default=100)
ap.add_argument("--goal-id", default=None)
args = ap.parse_args()

result = CEOGoalDecomposer().decompose(
    goal=args.goal,
    priority_base=args.priority_base,
    goal_id=args.goal_id,
)

print(json.dumps(asdict(result), indent=2))
print("PHASE96_RUNTIME_GOAL_SUBMIT: PASS")
