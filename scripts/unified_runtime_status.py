#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase705_720 import CEORuntimeBridge, UnifiedRuntimeStatus

root = Path.home() / "companyos"
print(json.dumps({
    "runtime": UnifiedRuntimeStatus().status(),
    "systems": CEORuntimeBridge(root).systems(),
}, indent=2))
