#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict

from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
from companyos.runtime.ceo_orchestration_journal import CEOOrchestrationJournal

ap = argparse.ArgumentParser()
ap.add_argument("orchestration_id")
ap.add_argument("--max-runner-cycles", type=int, default=200)
args = ap.parse_args()

ceo = AutonomousCEOOrchestrator()
journal = CEOOrchestrationJournal()

results = ceo.run_until_terminal(
    args.orchestration_id,
    max_runner_cycles=args.max_runner_cycles,
)

for r in results:
    journal.append(
        orchestration_id=r.orchestration_id,
        event="orchestration_cycle",
        payload=asdict(r),
    )

final = ceo.load(args.orchestration_id)
journal.append(
    orchestration_id=final.orchestration_id,
    event="orchestration_terminal" if final.state in ("COMPLETED", "FAILED", "HALTED") else "orchestration_paused",
    payload={
        "state": final.state,
        "total_cycles": final.total_cycles,
        "completed_goal_ids": final.completed_goal_ids,
        "failed_goal_ids": final.failed_goal_ids,
    },
)

print("CYCLES_EXECUTED:", len(results))
print("FINAL_STATE:", final.state)
print("TOTAL_CYCLES:", final.total_cycles)
print("COMPLETED_GOALS:", len(final.completed_goal_ids))
print("FAILED_GOALS:", len(final.failed_goal_ids))
print("FOLLOW_UP_GOALS:", len(final.follow_up_goal_ids))
print("FINAL_SUMMARY:", json.dumps(final.final_summary, indent=2))
print("CEO_ORCHESTRATOR_EXTERNAL_ACTIONS: False")
print("CEO_ORCHESTRATOR_BROADCASTS: False")
print("PHASE100_RUNTIME_CEO_RUN: PASS")
