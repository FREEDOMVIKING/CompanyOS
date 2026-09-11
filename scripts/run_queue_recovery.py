#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from companyos_phase809_824 import CEOQueueRecoveryBridge

p = argparse.ArgumentParser()
p.add_argument("--max-recoveries", type=int, default=3)
args = p.parse_args()

root = Path.home() / "companyos"
result = CEOQueueRecoveryBridge(root).run_once(max_recoveries=args.max_recoveries)
print(json.dumps(result, indent=2, default=str))
