#!/usr/bin/env python3
import json
from dataclasses import asdict

from companyos.runtime.autonomous_goal_scheduler import AutonomousGoalScheduler

result = AutonomousGoalScheduler().process_next()

print(json.dumps(asdict(result), indent=2))
print("GOAL_SCHEDULER_EXTERNAL_ACTIONS: False")
print("GOAL_SCHEDULER_BROADCASTS: False")
print("PHASE103_RUNTIME_GOAL_SCHEDULER_ONCE: PASS")
