#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from companyos.ceointelligence import AutonomousCEOOrchestrator
from companyos.daemonops import DurableJobQueue
from companyos.workerops import DurableWorkerPool

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("objective", nargs="?", default="Identify the highest-value internal improvement CompanyOS should work on next.")
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--max-jobs", type=int, default=25)
    args = ap.parse_args()

    root = Path.home() / "companyos"
    queue = DurableJobQueue(root)
    ceo = AutonomousCEOOrchestrator(root)

    plan = ceo.plan_and_delegate(
        args.objective,
        queue,
        context={
            "authority": "autonomous internal work only; consequential external actions require approval",
            "runtime": "CompanyOS Phase 17000"
        }
    )
    output = {"plan_cycle": plan}

    if plan.get("success") and not args.plan_only:
        output["execution_cycle"] = ceo.execute_delegated(
            queue,
            DurableWorkerPool(root),
            max_jobs=args.max_jobs
        )

    print(json.dumps(output, indent=2, default=str))

if __name__ == "__main__":
    main()
