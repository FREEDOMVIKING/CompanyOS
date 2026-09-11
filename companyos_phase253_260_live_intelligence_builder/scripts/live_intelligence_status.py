#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase253_260 import LiveIntelligenceRuntime

print(json.dumps(LiveIntelligenceRuntime(Path.home() / "companyos").status(), indent=2))
