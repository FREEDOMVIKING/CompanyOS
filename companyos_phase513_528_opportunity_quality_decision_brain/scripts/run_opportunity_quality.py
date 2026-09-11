#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase513_528 import CEOQualityBridge

root = Path.home() / "companyos"
print(json.dumps(CEOQualityBridge(root).run(), indent=2, default=str))
