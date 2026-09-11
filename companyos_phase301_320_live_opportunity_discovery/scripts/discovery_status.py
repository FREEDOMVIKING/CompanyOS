#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase301_320 import DiscoveryRuntime

print(json.dumps(DiscoveryRuntime(Path.home() / "companyos").status(), indent=2))
