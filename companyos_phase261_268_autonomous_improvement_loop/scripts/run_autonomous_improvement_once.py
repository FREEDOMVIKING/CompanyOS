#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase261_268 import AutonomousImprover

root = Path.home() / "companyos"
result = AutonomousImprover(root).run_once()
print(json.dumps(result, indent=2, default=str))
