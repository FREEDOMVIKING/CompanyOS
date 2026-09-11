#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict

from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
from companyos.runtime.ceo_orchestration_journal import CEOOrchestrationJournal

ap = argparse.ArgumentParser()
ap.add_argument("goal")
ap.add_argument("--orchestration-id", default=None)
ap.add_argument("--max-cycles", type=int, default=100)
ap.add_argument("--max-follow-up-depth", type=int, default=2)
args = ap.parse_args()

ceo = AutonomousCEOOrchestrator()
record = ceo.start(
    goal=args.goal,
    orchestration_id=args.orchestration_id,
    max_cycles=args.max_cycles,
    max_follow_up_depth=args.max_follow_up_depth,
)

CEOOrchestrationJournal().append(
    orchestration_id=record.orchestration_id,
    event="orchestration_started",
    payload={
        "root_goal_id": record.root_goal_id,
        "root_goal": record.root_goal,
    },
)

print(json.dumps(asdict(record), indent=2))
print("PHASE100_RUNTIME_CEO_SUBMIT: PASS")
