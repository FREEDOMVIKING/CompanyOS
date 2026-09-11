#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase301_320 import EvidenceStore
from companyos_phase369_384 import OpportunityIntelligenceCycle

root = Path.home() / "companyos"
records = EvidenceStore(root).read_recent(limit=500)
result = OpportunityIntelligenceCycle().run(records)
print(json.dumps(result, indent=2, default=str))
