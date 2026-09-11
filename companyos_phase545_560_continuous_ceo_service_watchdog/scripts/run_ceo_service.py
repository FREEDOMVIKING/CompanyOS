#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from companyos_phase545_560 import AutonomousCEOService

p = argparse.ArgumentParser()
p.add_argument("--max-ticks", type=int, default=None)
args = p.parse_args()

root = Path.home() / "companyos"
result = AutonomousCEOService(root).run(max_ticks=args.max_ticks)
print(json.dumps(result, indent=2, default=str))
