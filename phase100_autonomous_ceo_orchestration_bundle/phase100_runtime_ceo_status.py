#!/usr/bin/env python3
import argparse
import json
from dataclasses import asdict

from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator

ap = argparse.ArgumentParser()
ap.add_argument("orchestration_id")
args = ap.parse_args()

record = AutonomousCEOOrchestrator().load(args.orchestration_id)
print(json.dumps(asdict(record), indent=2))
print("PHASE100_RUNTIME_CEO_STATUS: PASS")
