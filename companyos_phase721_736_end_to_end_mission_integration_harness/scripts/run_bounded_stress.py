#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from companyos_phase721_736 import StressRunner

p=argparse.ArgumentParser()
p.add_argument("--rounds",type=int,default=3)
args=p.parse_args()

root=Path.home()/"companyos"
print(json.dumps(StressRunner(root).run(args.rounds),indent=2,default=str))
