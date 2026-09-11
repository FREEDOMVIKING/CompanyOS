#!/usr/bin/env python3
import argparse
from companyos.walletintegration.production_runtime_supervisor import ProductionRuntimeSupervisor

ap = argparse.ArgumentParser()
ap.add_argument("--interval", type=float, default=20.0)
ap.add_argument("--max-failures", type=int, default=5)
args = ap.parse_args()

sup = ProductionRuntimeSupervisor(
    interval_seconds=args.interval,
    max_consecutive_failures=args.max_failures,
)

try:
    sup.run_forever()
except KeyboardInterrupt:
    print()
    print("COMPANYOS_PRODUCTION_RUNTIME_SUPERVISOR: STOPPED_BY_USER")
