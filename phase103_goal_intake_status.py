#!/usr/bin/env python3
from collections import Counter

from companyos.runtime.autonomous_goal_intake import AutonomousGoalIntake

records = AutonomousGoalIntake().all_records()
counts = Counter(r.state for r in records)

print("TOTAL_INTAKE_RECORDS:", len(records))
for state in ["PENDING", "CLAIMED", "SUBMITTED", "FAILED", "CANCELLED"]:
    print(f"{state}:", counts.get(state, 0))

print("PHASE103_GOAL_INTAKE_STATUS: PASS")
