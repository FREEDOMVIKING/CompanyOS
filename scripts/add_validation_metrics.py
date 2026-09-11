#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from companyos_phase481_496 import ValidationMetricsStore

p = argparse.ArgumentParser()
p.add_argument("key")
p.add_argument("json_metrics")
args = p.parse_args()

metrics = json.loads(args.json_metrics)
store = ValidationMetricsStore(Path.home() / "companyos")
print(json.dumps(store.put(args.key, metrics), indent=2))
