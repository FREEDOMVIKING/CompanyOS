#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase277_284 import SupervisorRuntime

root = Path.home() / "companyos"
print(json.dumps(SupervisorRuntime(root).status(), indent=2))
