#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from companyos_phase481_496 import PersistentScheduler

p = argparse.ArgumentParser()
p.add_argument("--max-missions", type=int, default=3)
args = p.parse_args()

root = Path.home() / "companyos"
print(json.dumps(PersistentScheduler(root).run_once(args.max_missions), indent=2, default=str))
