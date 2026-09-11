#!/usr/bin/env python3
import argparse
from pathlib import Path
from companyos.autonomyops import AutonomousLoop
from companyos.ceointelligence import AutonomousCEOOrchestrator
from companyos.daemonops import DurableJobQueue
from companyos.workerops import DurableWorkerPool
from companyos.runtimeops import AutonomyDaemon

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--max-jobs", type=int, default=25)
    ap.add_argument("--max-cycles", type=int, default=None)
    args = ap.parse_args()

    root = Path.home() / "companyos"
    queue = DurableJobQueue(root)
    ceo = AutonomousCEOOrchestrator(root)
    pool = DurableWorkerPool(root)
    loop = AutonomousLoop(root, ceo, queue, pool)

    result = AutonomyDaemon(
        root,
        loop,
        interval_seconds=args.interval
    ).run_forever(
        max_jobs=args.max_jobs,
        max_cycles=args.max_cycles
    )
    print(result)

if __name__ == "__main__":
    main()
