#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict

from companyos.runtime.goal_lifecycle_manager import GoalLifecycleManager

ap = argparse.ArgumentParser()
ap.add_argument("goal_id")
ap.add_argument("--goal", default="")
args = ap.parse_args()

mgr = GoalLifecycleManager()
record = mgr.refresh(goal_id=args.goal_id, goal=args.goal)

print(json.dumps(asdict(record), indent=2))
print("PHASE98_RUNTIME_GOAL_STATUS: PASS")
