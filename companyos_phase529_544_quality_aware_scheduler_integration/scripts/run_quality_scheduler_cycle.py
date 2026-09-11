#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase529_544 import CEOQualityScheduler, IntegrationHealth

root = Path.home() / "companyos"
result = CEOQualityScheduler(root).run()
result["integration_health"] = IntegrationHealth().evaluate(result)
print(json.dumps(result, indent=2, default=str))
