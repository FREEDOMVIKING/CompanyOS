#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase321_336 import CEOResearchBridge

root = Path.home() / "companyos"
print(json.dumps(CEOResearchBridge(root).run(), indent=2, default=str))
