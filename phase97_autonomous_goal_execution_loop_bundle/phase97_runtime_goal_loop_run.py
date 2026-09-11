#!/usr/bin/env python3
import argparse
import time

from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop

ap = argparse.ArgumentParser()
ap.add_argument("--interval", type=float, default=10.0)
args = ap.parse_args()

loop = AutonomousGoalExecutionLoop()

print("COMPANYOS_AUTONOMOUS_GOAL_EXECUTION_LOOP: STARTED")
print("GOAL_LOOP_BROADCASTS: False")

try:
    while True:
        r = loop.cycle()
        print(
            f"DISPATCHED={r.dispatched} "
            f"AGENT={r.agent_name} "
            f"STATE={r.state} "
            f"REASON={r.reason} "
            f"COMPLETED={r.completed_tasks} "
            f"FAILED={r.failed_tasks} "
            f"QUEUED={r.queued_tasks} "
            f"RUNNING={r.running_tasks}"
        )
        time.sleep(max(2.0, args.interval))
except KeyboardInterrupt:
    print()
    print("COMPANYOS_AUTONOMOUS_GOAL_EXECUTION_LOOP: STOPPED_BY_USER")
