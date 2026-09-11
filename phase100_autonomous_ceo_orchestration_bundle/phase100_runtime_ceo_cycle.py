#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict

from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
from companyos.runtime.ceo_orchestration_journal import CEOOrchestrationJournal

ap = argparse.ArgumentParser()
ap.add_argument("orchestration_id")
args = ap.parse_args()

ceo = AutonomousCEOOrchestrator()
result = ceo.cycle(args.orchestration_id)

CEOOrchestrationJournal().append(
    orchestration_id=result.orchestration_id,
    event="orchestration_cycle",
    payload=asdict(result),
)

print(json.dumps(asdict(result), indent=2))
print("PHASE100_RUNTIME_CEO_CYCLE: PASS")
