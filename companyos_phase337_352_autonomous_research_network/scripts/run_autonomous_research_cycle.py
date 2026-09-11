#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase337_352 import AutonomousResearchCycle

root = Path.home() / "companyos"
print(json.dumps(AutonomousResearchCycle(root).run(), indent=2, default=str))
