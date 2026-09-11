#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase497_512 import CEOSchedulerBridge

root = Path.home() / "companyos"
print(json.dumps(CEOSchedulerBridge(root).run_tick(), indent=2, default=str))
