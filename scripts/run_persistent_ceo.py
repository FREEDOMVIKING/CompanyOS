#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from companyos_phase465_480 import PersistentCEO

parser = argparse.ArgumentParser()
parser.add_argument("--cycles", type=int, default=1)
args = parser.parse_args()

root = Path.home() / "companyos"
result = PersistentCEO(root).run(cycles=args.cycles)
print(json.dumps(result, indent=2, default=str))
