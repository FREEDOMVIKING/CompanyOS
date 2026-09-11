#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from companyos_phase481_496 import OperationsMetricsStore

p = argparse.ArgumentParser()
p.add_argument("venture_id")
p.add_argument("json_metrics")
args = p.parse_args()

metrics = json.loads(args.json_metrics)
store = OperationsMetricsStore(Path.home() / "companyos")
print(json.dumps(store.put(args.venture_id, metrics), indent=2))
