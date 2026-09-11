#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase337_352 import StarterResearchNetwork

root = Path.home() / "companyos"
print(json.dumps(StarterResearchNetwork(root).install_if_missing(), indent=2))
