#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase705_720 import CEORuntimeBridge

root = Path.home() / "companyos"
print(json.dumps(CEORuntimeBridge(root).tick(), indent=2, default=str))
