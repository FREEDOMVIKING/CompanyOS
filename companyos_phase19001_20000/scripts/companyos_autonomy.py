#!/usr/bin/env python3
import argparse, json
from pathlib import Path

from companyos.autonomyops import AutonomousLoop
from companyos.ceointelligence import AutonomousCEOOrchestrator
from companyos.daemonops import DurableJobQueue
from companyos.workerops import DurableWorkerPool

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--objective", default=None)
    ap.add_argument("--cycles", type=int, default=1)
    ap.add_argument("--max-jobs", type=int, default=25)
    args = ap.parse_args()

    root = Path.home() / "companyos"
    queue = DurableJobQueue(root)
    ceo = AutonomousCEOOrchestrator(root)
    pool = DurableWorkerPool(root)
    loop = AutonomousLoop(root, ceo, queue, pool)

    results = []
    for i in range(max(1, args.cycles)):
        results.append(loop.run_cycle(
            objective=args.objective if i == 0 else None,
            max_jobs=args.max_jobs
        ))

    print(json.dumps({
        "success": True,
        "status": "autonomy_cycles_complete",
        "cycles": results
    }, indent=2, default=str))

if __name__ == "__main__":
    main()
