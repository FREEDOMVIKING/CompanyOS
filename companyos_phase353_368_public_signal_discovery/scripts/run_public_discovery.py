#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase353_368 import CEOPublicResearch

root = Path.home() / "companyos"
print(json.dumps(CEOPublicResearch(root).run(), indent=2, default=str))
