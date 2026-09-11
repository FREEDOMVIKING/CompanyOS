#!/usr/bin/env python3
import argparse

from companyos.runtime.autonomous_ceo_runtime_service import AutonomousCEORuntimeService

ap = argparse.ArgumentParser()
ap.add_argument("--interval", type=float, default=10.0)
ap.add_argument("--max-failures", type=int, default=5)
args = ap.parse_args()

service = AutonomousCEORuntimeService(
    interval_seconds=args.interval,
    max_consecutive_failures=args.max_failures,
)

try:
    service.run_forever()
except KeyboardInterrupt:
    print()
    print("COMPANYOS_AUTONOMOUS_CEO_RUNTIME_SERVICE: STOPPED_BY_USER")
