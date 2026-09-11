#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from companyos_phase285_292 import PersistentImprover

parser = argparse.ArgumentParser()
parser.add_argument("--rounds", type=int, default=1)
parser.add_argument("--sleep-between", action="store_true")
args = parser.parse_args()

root = Path.home() / "companyos"
result = PersistentImprover(root).run(
    max_rounds=args.rounds,
    sleep_between=args.sleep_between,
)
print(json.dumps(result, indent=2, default=str))
