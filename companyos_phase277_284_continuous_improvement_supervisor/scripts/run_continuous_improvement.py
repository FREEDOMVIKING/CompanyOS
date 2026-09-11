#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase277_284 import ContinuousSupervisor

root = Path.home() / "companyos"
result = ContinuousSupervisor(root).run()
print(json.dumps(result, indent=2, default=str))
