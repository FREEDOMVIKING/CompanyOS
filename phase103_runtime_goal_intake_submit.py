#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict

from companyos.runtime.autonomous_goal_intake import AutonomousGoalIntake

ap = argparse.ArgumentParser()
ap.add_argument("goal")
ap.add_argument("--priority", type=int, default=100)
ap.add_argument("--intake-id", default=None)
args = ap.parse_args()

record = AutonomousGoalIntake().submit(
    goal=args.goal,
    priority=args.priority,
    intake_id=args.intake_id,
)

print(json.dumps(asdict(record), indent=2))
print("PHASE103_RUNTIME_GOAL_INTAKE_SUBMIT: PASS")
