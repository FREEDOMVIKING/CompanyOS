#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict

from companyos.runtime.policy_guarded_goal_intake import PolicyGuardedGoalIntake

ap = argparse.ArgumentParser()
ap.add_argument("goal")
ap.add_argument("--priority", type=int, default=100)
ap.add_argument("--source", default="manual")
ap.add_argument("--intake-id", default=None)
args = ap.parse_args()

result = PolicyGuardedGoalIntake().submit(
    goal=args.goal,
    priority=args.priority,
    source=args.source,
    intake_id=args.intake_id,
)

print(json.dumps(asdict(result), indent=2))
print("PHASE105_RUNTIME_GOAL_SUBMIT: PASS")
