#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase261_268 import ContinuousImprovementRuntime

root = Path.home() / "companyos"
print(json.dumps(ContinuousImprovementRuntime(root).status(), indent=2))
